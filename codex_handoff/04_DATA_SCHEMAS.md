# Data Schemas

아래는 구현 의도를 보여주는 TypeScript 형태다. 실제 구현은 Zod schema를
source of truth로 사용한다.

``` ts
type UserProfile = {
  age?: number | null;
  birthYear?: number | null;
  location?: string | null;
  occupation?: string | null;

  carrier?: {
    provider: string;
    grade?: string | null;
  } | null;

  cards: {
    issuer: string;
    product: string;
  }[];

  memberships: string[];
};

type PurchaseIntent = {
  merchant: string;
  product: string | null;
  date: string | null;
  location: string | null;
  quantity: number | null;
};

type SearchCategory =
  | "card"
  | "carrier"
  | "membership"
  | "age"
  | "occupation"
  | "location"
  | "promotion";

type SearchTask = {
  id: string;
  category: SearchCategory;
  query: string;
  profileEvidence: string[];
  mode: "personal" | "discovery";
};

type Requirement = {
  field: string;
  operator:
    | "equals"
    | "contains"
    | "gte"
    | "lte"
    | "in"
    | "unknown";
  value: string | number | string[];
  description: string;
};

type BenefitCandidate = {
  id: string;
  title: string;
  merchant: string;
  provider: string;

  category:
    | SearchCategory
    | "other";

  discount: {
    type:
      | "percentage"
      | "fixed"
      | "special_price"
      | "unknown";
    value: number | null;
    specialPrice: number | null;
  };

  requirements: Requirement[];

  validFrom: string | null;
  validUntil: string | null;
  purchaseMethod: string | null;
  stackable: boolean | null;

  source: {
    url: string;
    title: string;
    official: boolean;
    retrievedAt: string;
  };

  confidence: "high" | "medium" | "low";
};

type EligibilityStatus =
  | "confirmed"
  | "needs_info"
  | "not_eligible"
  | "unknown";

type EvaluatedBenefit = BenefitCandidate & {
  eligibility: {
    status: EligibilityStatus;
    matched: string[];
    missing: {
      field: string;
      question: string;
    }[];
    failed: string[];
  };

  originalPrice: number | null;
  finalPrice: number | null;
  savedAmount: number | null;
};

type BasePrice = {
  amount: number;
  currency: "KRW";
  product: string | null;
  priceType: string | null;
  date: string | null;
  source: {
    url: string;
    title: string;
    official: boolean;
  };
};

type SearchResponse = {
  merchant: string;
  basePrice: BasePrice | null;

  summary: {
    searched: number;
    found: number;
    confirmed: number;
    needsInfo: number;
  };

  best: EvaluatedBenefit | null;
  alternatives: EvaluatedBenefit[];
  opportunities: EvaluatedBenefit[];
};
```

## Mock profile

초기 PoC에서는 DB 없이 다음 프로필을 고정해도 된다.

``` ts
export const mockProfile: UserProfile = {
  age: 26,
  birthYear: 2000,
  location: "서울",
  occupation: "대학생",
  carrier: {
    provider: "SKT",
    grade: null,
  },
  cards: [
    {
      issuer: "현대카드",
      product: "ZERO Edition3",
    },
  ],
  memberships: ["네이버플러스"],
};
```
