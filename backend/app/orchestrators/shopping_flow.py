from app.api.schemas.common import (
    ProviderStatusPayload,
    RecommendationDebugPayload,
    RecommendationPayload,
    UserQueryPayload,
    WorkflowStepStatus,
    WorkflowTrace,
)
from app.api.schemas.request import ChatRequest, RecommendRequest
from app.domain.constants import WORKFLOW_ORDER
from app.ports.logger_port import LoggerPort
from app.usecases.analyze_intent import AnalyzeIntentUseCase
from app.usecases.build_search_strategy import BuildSearchStrategyUseCase
from app.usecases.filter_evidence import FilterEvidenceUseCase
from app.usecases.generate_candidates import GenerateCandidatesUseCase
from app.usecases.generate_recommendation import GenerateRecommendationUseCase
from app.usecases.retrieve_expert_signals import RetrieveExpertSignalsUseCase
from app.usecases.retrieve_products import RetrieveProductsUseCase
from app.usecases.summarize_results import SummarizeResultsUseCase


class ShoppingFlowOrchestrator:
    def __init__(
        self,
        analyze_intent_use_case: AnalyzeIntentUseCase,
        build_search_strategy_use_case: BuildSearchStrategyUseCase,
        retrieve_expert_signals_use_case: RetrieveExpertSignalsUseCase,
        generate_candidates_use_case: GenerateCandidatesUseCase,
        retrieve_products_use_case: RetrieveProductsUseCase,
        filter_evidence_use_case: FilterEvidenceUseCase,
        summarize_results_use_case: SummarizeResultsUseCase,
        generate_recommendation_use_case: GenerateRecommendationUseCase,
        logger: LoggerPort,
        providers: ProviderStatusPayload,
    ) -> None:
        self._analyze_intent = analyze_intent_use_case
        self._build_search_strategy = build_search_strategy_use_case
        self._retrieve_expert_signals = retrieve_expert_signals_use_case
        self._generate_candidates = generate_candidates_use_case
        self._retrieve_products = retrieve_products_use_case
        self._filter_evidence = filter_evidence_use_case
        self._summarize_results = summarize_results_use_case
        self._generate_recommendation = generate_recommendation_use_case
        self._logger = logger
        self._providers = providers

    def run_chat(self, request: ChatRequest) -> tuple[RecommendationPayload, WorkflowTrace]:
        user_query = UserQueryPayload(
            query=request.message,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            constraints=request.constraints,
            max_candidates=request.max_candidates,
            session_id=request.session_id,
        )
        return self._run(user_query)

    def run_recommendation(
        self, request: RecommendRequest
    ) -> tuple[RecommendationPayload, WorkflowTrace]:
        user_query = UserQueryPayload(
            query=request.query,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            constraints=request.constraints,
            max_candidates=request.max_candidates,
        )
        return self._run(user_query)

    def _run(self, user_query: UserQueryPayload) -> tuple[RecommendationPayload, WorkflowTrace]:
        steps: list[WorkflowStepStatus] = []
        self._logger.info("Running shopping flow")

        intent = self._analyze_intent.execute(user_query)
        steps.append(WorkflowStepStatus(step="analyze_intent"))

        strategy = self._build_search_strategy.execute(intent, user_query.max_candidates)
        steps.append(WorkflowStepStatus(step="build_search_strategy"))

        expert_signals = self._retrieve_expert_signals.execute(strategy)
        steps.append(WorkflowStepStatus(step="retrieve_expert_signals"))

        candidate_generation = self._generate_candidates.execute(
            intent=intent,
            expert_signals=expert_signals,
            max_candidates=user_query.max_candidates,
        )
        steps.append(WorkflowStepStatus(step="generate_candidates"))

        retrieval = self._retrieve_products.execute(candidate_generation)
        steps.append(WorkflowStepStatus(step="retrieve_products"))

        filtered = self._filter_evidence.execute(intent, retrieval)
        steps.append(WorkflowStepStatus(step="filter_evidence"))

        summary = self._summarize_results.execute(intent, filtered)
        steps.append(WorkflowStepStatus(step="summarize_results"))

        recommendation = self._generate_recommendation.execute(
            intent=intent,
            filtered=filtered,
            summary=summary,
            max_candidates=user_query.max_candidates,
        )
        recommendation = recommendation.model_copy(
            update={
                "debug": RecommendationDebugPayload(
                    expert_signal_source_mode=self._summarize_expert_signal_mode(expert_signals.signals),
                    expert_signals=expert_signals.signals,
                    generated_candidates=candidate_generation.candidates,
                )
            }
        )
        steps.append(WorkflowStepStatus(step="generate_recommendation"))

        workflow = WorkflowTrace(
            workflow_order=list(WORKFLOW_ORDER),
            steps=steps,
            providers=self._providers,
        )
        return recommendation, workflow

    @staticmethod
    def _summarize_expert_signal_mode(signals) -> str:
        if not signals:
            return "none"
        has_live = any(signal.retrieval_source == "serpapi_live" for signal in signals)
        has_fallback = any(signal.retrieval_source.startswith("mock") for signal in signals)
        if has_live and has_fallback:
            return "mixed"
        if has_live:
            return "live"
        if has_fallback:
            return "fallback"
        return "unknown"
