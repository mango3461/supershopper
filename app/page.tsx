import Link from 'next/link';
import {
  ArrowUpRight,
  Check,
  CreditCard,
  ScanLine,
  ShieldCheck,
  Sparkles,
  Ticket,
  Fingerprint,
  ArrowRight,
} from 'lucide-react';
import { SearchBar } from '../components/SearchBar';
import { ProfileSummary } from '../components/ProfileSummary';
export default function Home() {
  return (
    <main id="main" className="home">
      <section className="hero">
        <div className="hero-copy">
          <div className="hero-label">
            <span />
            나를 위한 가격 검색, 슈퍼쇼퍼
          </div>
          <h1>
            정가는 같아도,
            <br />
            <span>내 가격</span>은 다르니까.
          </h1>
          <p className="hero-description">
            카드부터 통신사, 멤버십까지.
            <br />
            내가 받을 수 있는 할인을 한 번에 찾아보세요.
          </p>
          <SearchBar />
          <div className="suggestions">
            <span>먼저 찾아보세요</span>
            <Link href="/search?q=에버랜드">
              에버랜드 <ArrowUpRight size={13} />
            </Link>
            <span className="soon-chip">
              CGV · KTX · 스타벅스 <small>웹 검색 모드</small>
            </span>
          </div>
          <div className="hero-trust">
            <ShieldCheck size={16} />
            공식 출처로 확인하고, 확실한 가격만 계산해요.
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <span className="art-plus">✳</span>
          <div className="floating-tag tag-top">
            <CreditCard size={18} />
            내가 가진 카드
            <Check size={15} />
          </div>
          <div className="price-ticket">
            <div className="ticket-top">
              <span>JUST FOR YOU</span>
              <Sparkles size={21} />
            </div>
            <div className="ticket-main">
              <span>모두의 정가에서</span>
              <strong>
                나만의
                <br />
                가격으로<span>↘</span>
              </strong>
            </div>
            <div className="ticket-bottom">
              <Fingerprint size={32} />
              <span>
                내 혜택으로 찾는
                <br />
                <b>더 똑똑한 선택</b>
              </span>
              <ScanLine size={35} />
            </div>
          </div>
          <div className="floating-tag tag-bottom">
            <Ticket size={19} />
            <div>
              놓치고 있던 혜택까지.<small>지금, 함께 찾아볼까요?</small>
            </div>
            <ArrowUpRight size={17} />
          </div>
          <span className="art-caption">SAME PRICE? NOT FOR YOU.</span>
        </div>
      </section>
      <div className="home-bottom">
        <ProfileSummary home />
        <section className="how-section">
          <span className="eyebrow">LESS SEARCH. BETTER PRICE.</span>
          <h2>
            할인 찾는 수고는 줄이고,
            <br />
            나에게 맞는 선택을.
          </h2>
          <div className="how-steps">
            <div>
              <span>01</span>
              <p>
                <b>내 혜택을 알려주세요</b>
                <small>카드, 통신사, 멤버십만 간단히.</small>
              </p>
            </div>
            <div>
              <span>02</span>
              <p>
                <b>가고 싶은 곳을 검색하세요</b>
                <small>공식 출처에서 할인 경로를 탐색해요.</small>
              </p>
            </div>
            <div>
              <span>03</span>
              <p>
                <b>조건을 확인하고 선택하세요</b>
                <small>적용 여부부터 공식 구매처까지.</small>
              </p>
            </div>
          </div>
          <Link href="/search?q=에버랜드" className="text-link">
            에버랜드에서 시작하기
            <ArrowRight size={16} />
          </Link>
        </section>
      </div>
    </main>
  );
}
