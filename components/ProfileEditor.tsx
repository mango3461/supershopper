'use client';
import Link from 'next/link';
import { useState } from 'react';
import {
  BadgeCheck,
  Check,
  CreditCard,
  Plus,
  Smartphone,
  Trash2,
  UserRound,
  ArrowRight,
} from 'lucide-react';
import { profileSchema, type UserProfile } from '../schemas';
import { saveProfile, useProfile } from '../lib/profile/store';
export function ProfileEditor() {
  const { profile, isDemo } = useProfile();
  const [saved, setSaved] = useState(false);
  return (
    <ProfileForm
      key={JSON.stringify(profile)}
      initial={profile}
      isDemo={isDemo}
      saved={saved}
      setSaved={setSaved}
    />
  );
}
function ProfileForm({
  initial,
  isDemo,
  saved,
  setSaved,
}: {
  initial: UserProfile;
  isDemo: boolean;
  saved: boolean;
  setSaved: (saved: boolean) => void;
}) {
  const [profile, setProfile] = useState(initial);
  const [memberships, setMemberships] = useState(initial.memberships.join(', '));
  const [error, setError] = useState('');
  function update(p: Partial<UserProfile>) {
    setProfile({ ...profile, ...p });
    setSaved(false);
  }
  return (
    <form
      className="profile-form"
      onSubmit={(e) => {
        e.preventDefault();
        const parsed = profileSchema.safeParse({
          ...profile,
          memberships: memberships
            .split(',')
            .map((v) => v.trim())
            .filter(Boolean),
        });
        if (!parsed.success) {
          setError('나이와 입력 정보를 확인해주세요.');
          return;
        }
        try {
          saveProfile(parsed.data);
          setSaved(true);
          setError('');
        } catch {
          setError('브라우저 저장소를 사용할 수 없어요. 저장소 설정을 확인해주세요.');
        }
      }}
    >
      {isDemo && (
        <div className="notice">
          <UserRound size={18} />
          <p>현재 예시 프로필이에요. 실제 보유한 혜택으로 수정해주세요.</p>
        </div>
      )}
      <section className="form-section">
        <h2>
          <CreditCard size={21} />내 카드<span>정확한 상품명을 입력해주세요</span>
        </h2>
        {profile.cards.map((card, i) => (
          <div className="card-input-row" key={i}>
            <label>
              카드사
              <input
                aria-label={`카드사 ${i + 1}`}
                value={card.issuer}
                placeholder="현대카드"
                maxLength={100}
                required
                onChange={(e) =>
                  update({
                    cards: profile.cards.map((c, n) =>
                      n === i ? { ...c, issuer: e.target.value } : c,
                    ),
                  })
                }
              />
            </label>
            <label>
              카드 상품
              <input
                aria-label={`카드 상품 ${i + 1}`}
                list="card-products"
                value={card.product}
                placeholder="ZERO Edition3"
                maxLength={150}
                required
                onChange={(e) =>
                  update({
                    cards: profile.cards.map((c, n) =>
                      n === i ? { ...c, product: e.target.value } : c,
                    ),
                  })
                }
              />
            </label>
            <button
              className="icon-button"
              type="button"
              aria-label={`카드 ${i + 1} 삭제`}
              onClick={() => update({ cards: profile.cards.filter((_, n) => n !== i) })}
            >
              <Trash2 size={17} />
            </button>
          </div>
        ))}
        <datalist id="card-products">
          <option value="ZERO Edition3" />
          <option value="M" />
          <option value="에버랜드 삼성카드" />
        </datalist>
        <button
          type="button"
          className="add-button"
          disabled={profile.cards.length >= 20}
          onClick={() => update({ cards: [...profile.cards, { issuer: '', product: '' }] })}
        >
          <Plus size={16} />
          카드 추가
        </button>
        <small className="muted">
          목록에 없으면 보유한 상품명을 그대로 입력하세요. 카드사만 같아도 혜택은 다를 수 있어요.
        </small>
      </section>
      <section className="form-section">
        <h2>
          <Smartphone size={21} />내 통신사
        </h2>
        <div className="form-grid">
          <label>
            통신사
            <select
              value={profile.carrier?.provider || ''}
              onChange={(e) =>
                update({
                  carrier: e.target.value ? { provider: e.target.value, grade: null } : null,
                })
              }
            >
              <option value="">미등록</option>
              {['SKT', 'KT', 'LG U+', '알뜰폰'].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label>
            멤버십 등급
            <input
              value={profile.carrier?.grade || ''}
              placeholder="모르면 비워두세요"
              disabled={!profile.carrier}
              maxLength={100}
              onChange={(e) =>
                profile.carrier &&
                update({ carrier: { ...profile.carrier, grade: e.target.value || null } })
              }
            />
          </label>
        </div>
      </section>
      <section className="form-section">
        <h2>
          <BadgeCheck size={21} />내 멤버십
        </h2>
        <label>
          보유한 멤버십
          <input
            value={memberships}
            placeholder="네이버플러스, 쿠팡 와우"
            maxLength={500}
            onChange={(e) => {
              setMemberships(e.target.value);
              setSaved(false);
            }}
          />
        </label>
        <small className="muted">여러 개라면 쉼표로 구분해주세요.</small>
      </section>
      <section className="form-section">
        <h2>
          <UserRound size={21} />
          나의 조건<span>해당하는 항목만 알려주세요</span>
        </h2>
        <div className="form-grid">
          <label>
            만 나이
            <input
              type="number"
              min="0"
              max="120"
              value={profile.age ?? ''}
              placeholder="미등록"
              onChange={(e) =>
                update({
                  age: e.target.value === '' ? null : Number(e.target.value),
                  birthYear: null,
                })
              }
            />
          </label>
          <label>
            거주 지역
            <input
              value={profile.location || ''}
              placeholder="서울"
              maxLength={100}
              onChange={(e) => update({ location: e.target.value || null })}
            />
          </label>
          <label>
            직업·신분
            <select
              value={profile.occupation || ''}
              onChange={(e) => update({ occupation: e.target.value || null })}
            >
              <option value="">미등록</option>
              {['대학생', '대학원생', '직장인', '중고등학생', '군인', '기타'].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
        </div>
      </section>
      <div className="save-row">
        <p role="status">
          {error ||
            (saved ? '내 혜택을 저장했어요.' : '카드번호·주민번호·결제내역은 수집하지 않아요.')}
        </p>
        <button className="primary-button" type="submit">
          <Check size={18} />내 혜택 저장
        </button>
      </div>
      <Link className="text-link" href="/search?q=에버랜드">
        에버랜드 내 가격 찾아보기
        <ArrowRight size={16} />
      </Link>
    </form>
  );
}
