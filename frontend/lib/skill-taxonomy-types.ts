export interface SkillListItem {
  skill_id: string;

  domain_id: string;
  domain_slug: string;
  domain_name: string;

  category_id: string | null;
  category_slug: string | null;
  category_name: string | null;

  slug: string;
  name: string;
  description: string | null;

  skill_type: string;
  difficulty_level: string;

  tags: string[];

  is_active: boolean;
  is_deprecated: boolean;

  source: string;
}

export interface SkillCategoryTree {
  category_id: string;
  domain_id: string;
  parent_category_id: string | null;

  slug: string;
  name: string;
  description: string | null;
  display_order: number;

  skills: SkillListItem[];
  children: SkillCategoryTree[];
}

export interface SkillDomainTree {
  domain_id: string;
  slug: string;
  name: string;
  description: string | null;
  display_order: number;

  uncategorized_skills: SkillListItem[];
  categories: SkillCategoryTree[];
}

export interface SkillTaxonomyTree {
  domain_count: number;
  category_count: number;
  skill_count: number;

  domains: SkillDomainTree[];
}

export interface SkillAlias {
  alias_id: string;
  skill_id: string;
  alias: string;
  normalized_alias: string;
  alias_type: string;
  created_at: string;
}

export interface SkillRelationship {
  relationship_id: string;

  source_skill_id: string;
  source_skill_slug: string;
  source_skill_name: string;

  target_skill_id: string;
  target_skill_slug: string;
  target_skill_name: string;

  relationship_type: string;
  strength: number;

  notes: string | null;
  source: string;
  is_active: boolean;

  created_at: string;
  updated_at: string;
}

export interface SkillDetail {
  skill: SkillListItem;
  aliases: SkillAlias[];

  outgoing_relationships:
    SkillRelationship[];

  incoming_relationships:
    SkillRelationship[];

  superseded_by: SkillListItem | null;
}

export interface SkillSearchResponse {
  total: number;
  result_count: number;
  results: SkillListItem[];
}