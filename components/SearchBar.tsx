'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Search } from 'lucide-react';
export function SearchBar({
  initial = '',
  compact = false,
}: {
  initial?: string;
  compact?: boolean;
}) {
  const [value, setValue] = useState(initial);
  const router = useRouter();
  return (
    <form
      className={`search-bar ${compact ? 'compact' : ''}`}
      action="/search"
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim()) router.push(`/search?q=${encodeURIComponent(value.trim())}`);
      }}
    >
      <Search size={23} />
      <label className="sr-only" htmlFor={compact ? 'result-query' : 'home-query'}>
        어디에서 결제하시나요?
      </label>
      <input
        id={compact ? 'result-query' : 'home-query'}
        name="q"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="어디에서 결제하시나요?"
        required
        maxLength={300}
        autoComplete="off"
      />
      <button type="submit">
        <span>{compact ? '검색' : '내 가격 찾기'}</span>
        <ArrowRight size={19} />
      </button>
    </form>
  );
}
