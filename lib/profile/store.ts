'use client';
import { useMemo, useSyncExternalStore } from 'react';
import { profileSchema, type UserProfile } from '../../schemas';
import { mockProfile } from './mockProfile';
const key = 'supershopper-profile-v1';
const defaultSnapshot = JSON.stringify(mockProfile);
const subscribe = (callback: () => void) => {
  window.addEventListener('storage', callback);
  window.addEventListener('profile-change', callback);
  return () => {
    window.removeEventListener('storage', callback);
    window.removeEventListener('profile-change', callback);
  };
};
const snapshot = () => {
  try {
    return localStorage.getItem(key) || defaultSnapshot;
  } catch {
    return defaultSnapshot;
  }
};
export function useProfile() {
  const serialized = useSyncExternalStore(subscribe, snapshot, () => defaultSnapshot);
  const profile = useMemo(() => {
    try {
      return profileSchema.parse(JSON.parse(serialized));
    } catch {
      return mockProfile;
    }
  }, [serialized]);
  return { profile, isDemo: serialized === defaultSnapshot };
}
export function saveProfile(profile: UserProfile) {
  localStorage.setItem(key, JSON.stringify(profileSchema.parse(profile)));
  window.dispatchEvent(new Event('profile-change'));
}
