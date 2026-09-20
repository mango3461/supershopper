import OpenAI from 'openai';
import { zodTextFormat } from 'openai/helpers/zod';
import { z } from 'zod';
import { audit, safeFailure } from './audit';
export function createAi() {
  if (!process.env.OPENAI_API_KEY) throw new Error('OPENAI_NOT_CONFIGURED');
  return new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    timeout: 45000,
    maxRetries: 0,
    logLevel: 'off',
  });
}
export const model = () => process.env.OPENAI_MODEL || 'gpt-5-mini';
export async function structured<T extends z.ZodType>(
  client: OpenAI,
  schema: T,
  name: string,
  prompt: string,
  input: unknown,
  signal?: AbortSignal,
): Promise<z.infer<T>> {
  const started = Date.now();
  try {
    const response = await client.responses.parse(
      {
        model: model(),
        store: false,
        input: [
          { role: 'system', content: prompt },
          { role: 'user', content: JSON.stringify(input) },
        ],
        text: { format: zodTextFormat(schema, name) },
      },
      { signal },
    );
    if (response.status !== 'completed') throw new Error('MODEL_INCOMPLETE');
    const parsed = schema.parse(response.output_parsed);
    audit({
      stage: name,
      status: 'complete',
      model: response.model,
      latencyMs: Date.now() - started,
    });
    return parsed;
  } catch (e) {
    audit({
      stage: name,
      status: 'failed',
      model: /^gpt-[a-z0-9.-]+$/.test(model()) ? model() : undefined,
      ...safeFailure(e),
      latencyMs: Date.now() - started,
    });
    throw e;
  }
}
