import { ProfileEditor } from '../../components/ProfileEditor';
export default function ProfilePage() {
  return (
    <main id="main" className="profile-page">
      <span className="eyebrow">MY BENEFITS</span>
      <h1>
        내가 가진 혜택,
        <br />
        <span>빠짐없이 챙기세요.</span>
      </h1>
      <p className="page-description">
        카드번호나 결제정보는 필요하지 않아요.
        <br />
        등록한 정보는 이 브라우저에 저장돼요.
      </p>
      <ProfileEditor />
    </main>
  );
}
