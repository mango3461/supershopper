import type { UserProfile } from '../../schemas';
export const mockProfile: UserProfile = {
  age: 26,
  birthYear: 2000,
  location: '서울',
  occupation: '대학생',
  carrier: { provider: 'SKT', grade: null },
  cards: [{ issuer: '현대카드', product: 'ZERO Edition3' }],
  memberships: ['네이버플러스'],
};
