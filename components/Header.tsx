'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ArrowUpRight, ShoppingBag, UserRound } from 'lucide-react';
export function Header() {
  const path = usePathname();
  return (
    <header className="header">
      <Link className="brand" href="/" aria-label="슈퍼쇼퍼 홈">
        <span className="brand-icon">
          <ShoppingBag size={21} strokeWidth={2.2} />
        </span>
        supershopper<span className="brand-dot">.</span>
      </Link>
      <nav aria-label="메인 메뉴">
        <Link href="/" className={path !== '/profile' ? 'active' : ''}>
          내 가격 찾기
        </Link>
        <Link href="/profile" className={path === '/profile' ? 'active' : ''}>
          내 혜택<span className="desktop-only"> 관리</span>
        </Link>
      </nav>
      <Link href="/profile" className="header-profile">
        <UserRound size={17} />
        <span>내 혜택 등록</span>
        <ArrowUpRight size={15} />
      </Link>
    </header>
  );
}
