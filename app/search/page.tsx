import { SearchClient } from '../../components/SearchClient';
export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  return <SearchClient key={q} query={q?.slice(0, 300) || '에버랜드'} />;
}
