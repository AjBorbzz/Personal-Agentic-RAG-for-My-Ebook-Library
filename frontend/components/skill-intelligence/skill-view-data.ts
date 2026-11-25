import { skillAPI } from "@/lib/skill-intelligence-api";
import type {
  CareerTarget,
  CareerTargetSkill,
  Evidence,
  GapResponse,
  ProficiencyLevel,
  QueueItem,
  Recommendation,
  SkillState,
} from "@/lib/skill-intelligence-types";

export type Mode =
  | "overview"
  | "profile"
  | "skill"
  | "targets"
  | "target"
  | "recommendations"
  | "queue";
export type Props = { mode: Mode; skillId?: string; targetId?: string };
export type ViewAction = (
  action: () => Promise<unknown>,
  message: string,
) => Promise<void>;
export type ViewData = Partial<{
  states: SkillState[];
  levels: ProficiencyLevel[];
  targets: CareerTarget[];
  target: CareerTarget;
  requirements: CareerTargetSkill[];
  gaps: GapResponse;
  recommendations: Recommendation[];
  queue: QueueItem[];
  evidence: Evidence[];
}>;

export async function loadView(
  { mode, targetId, skillId }: Props,
  profileId: string,
  targetFilter: string,
  signal: AbortSignal,
): Promise<ViewData> {
  const options = { signal };

  switch (mode) {
    case "overview": {
      const [states, targets, gaps, recommendations, queue] = await Promise.all(
        [
          skillAPI.states(profileId, options),
          skillAPI.targets(profileId, options),
          skillAPI.gaps(profileId, undefined, options),
          skillAPI.recommendations(profileId, undefined, options),
          skillAPI.queue(profileId, options),
        ],
      );
      return { states, targets, gaps, recommendations, queue };
    }
    case "profile": {
      const [states, levels] = await Promise.all([
        skillAPI.states(profileId, options),
        skillAPI.levels(options),
      ]);
      return { states, levels };
    }
    case "skill": {
      if (!skillId) throw new Error("This skill link has no identifier.");
      const [states, levels, gaps, recommendations] = await Promise.all([
        skillAPI.states(profileId, options),
        skillAPI.levels(options),
        skillAPI.gaps(profileId, undefined, options),
        skillAPI.recommendations(profileId, undefined, options),
      ]);
      const evidence = states.some((state) => state.skill_id === skillId)
        ? await skillAPI.evidence(profileId, skillId, options)
        : [];
      return { states, levels, gaps, recommendations, evidence };
    }
    case "targets":
      return { targets: await skillAPI.targets(profileId, options) };
    case "target": {
      if (!targetId)
        throw new Error("This career target link has no identifier.");
      const target = await skillAPI.target(profileId, targetId, options);
      const [requirements, gaps, levels] = await Promise.all([
        skillAPI.requirements(profileId, targetId, options),
        skillAPI.gaps(profileId, targetId, options),
        skillAPI.levels(options),
      ]);
      return { target, requirements, gaps, levels };
    }
    case "recommendations": {
      const [targets, recommendations] = await Promise.all([
        skillAPI.targets(profileId, options),
        skillAPI.recommendations(profileId, targetFilter || undefined, options),
      ]);
      return { targets, recommendations };
    }
    case "queue":
      return { queue: await skillAPI.queue(profileId, options) };
  }
}
