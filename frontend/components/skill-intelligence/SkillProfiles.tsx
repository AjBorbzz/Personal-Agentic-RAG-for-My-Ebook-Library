"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { skillAPI } from "@/lib/skill-intelligence-api";
import type { Profile } from "@/lib/skill-intelligence-types";

type SkillProfiles = {
  profiles: Profile[] | null;
  activeProfiles: Profile[];
  profileId: string;
  loadError: string;
  selectProfile: (id: string) => void;
  addProfile: (profile: Profile) => void;
};

const ProfileContext = createContext<SkillProfiles | null>(null);

export function SkillProfileProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[] | null>(null);
  const [selectedProfileId, selectProfile] = useState("");
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    skillAPI
      .profiles({ signal: controller.signal })
      .then((rows) => {
        if (!controller.signal.aborted) setProfiles(rows);
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setLoadError(cause instanceof Error ? cause.message : String(cause));
        }
      });
    return () => controller.abort();
  }, []);

  const activeProfiles = profiles?.filter((profile) => profile.is_active) ?? [];
  const profileId =
    (
      activeProfiles.find(
        (profile) => profile.profile_id === selectedProfileId,
      ) ??
      activeProfiles.find((profile) => profile.is_default) ??
      activeProfiles[0]
    )?.profile_id ?? "";

  function addProfile(profile: Profile) {
    setProfiles((rows) => [...(rows ?? []), profile]);
    selectProfile(profile.profile_id);
  }

  return (
    <ProfileContext.Provider
      value={{
        profiles,
        activeProfiles,
        profileId,
        loadError,
        selectProfile,
        addProfile,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
}

export function useSkillProfiles() {
  const context = useContext(ProfileContext);
  if (!context)
    throw new Error("Skill profiles require the Skill Intelligence layout.");
  return context;
}
