'use client';
import Link from 'next/link';
import { CreditCard, Smartphone, BadgeCheck, UserRound, ArrowUpRight, Plus } from 'lucide-react';
import { useProfile } from '../lib/profile/store';
export function ProfileSummary({ home = false }: { home?: boolean }) {
  const { profile, isDemo } = useProfile();
  const groups = [
    {
      label: '카드',
      icon: CreditCard,
      values: profile.cards.map((c) => `${c.issuer} ${c.product}`),
    },
    {
      label: '통신사',
      icon: Smartphone,
      values: profile.carrier
        ? [`${profile.carrier.provider} · ${profile.carrier.grade || '등급 미등록'}`]
        : [],
    },
    { label: '멤버십', icon: BadgeCheck, values: profile.memberships },
    {
      label: '나의 조건',
      icon: UserRound,
      values: [
        profile.age != null ? `${profile.age}세` : '',
        profile.occupation,
        profile.location,
      ].filter((v): v is string => Boolean(v)),
    },
  ];
  return (
    <section className={`profile-summary ${home ? 'home-profile' : ''}`} aria-label="내 혜택">
      <div className="section-heading">
        <div>
          <span className="eyebrow">MY BENEFITS</span>
          <h2>이미 가진 혜택부터.</h2>
        </div>
        <Link href="/profile" className="icon-link" aria-label="내 혜택 수정">
          <ArrowUpRight size={21} />
        </Link>
      </div>
      {isDemo && <p className="demo-label">데모 프로필 · 내 정보로 바꿀 수 있어요</p>}
      <div className="profile-groups">
        {groups.map((group) => (
          <div className="profile-group" key={group.label}>
            <span className="group-icon">
              <group.icon size={19} />
            </span>
            <div>
              <span className="group-label">{group.label}</span>
              {group.values.length ? (
                group.values.map((v) => <p key={v}>{v}</p>)
              ) : (
                <p className="muted">아직 등록하지 않았어요</p>
              )}
            </div>
          </div>
        ))}
      </div>
      <Link className="profile-add" href="/profile">
        <Plus size={16} />내 혜택 추가·수정
      </Link>
      <p className="privacy-note">카드번호나 결제정보는 필요하지 않아요.</p>
    </section>
  );
}
