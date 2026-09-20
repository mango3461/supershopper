import type { Metadata } from 'next';
import { Header } from '../components/Header';
import './globals.css';
export const metadata: Metadata = {
  title: '슈퍼쇼퍼 — 정가는 같아도, 내 가격은 다르니까',
  description: '카드, 통신사, 멤버십부터 나만의 조건까지. 공식 근거로 확인하는 개인화 가격 검색.',
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <a className="skip-link" href="#main">
          본문으로 바로가기
        </a>
        <Header />
        {children}
        <footer className="footer">
          <span className="brand-small">
            supershopper<span>®</span>
          </span>
          <span>좋은 소비의 시작, 내게 맞는 가격.</span>
          <span>공식 출처 기반 · 해커톤 MVP</span>
        </footer>
      </body>
    </html>
  );
}
