INSERT INTO proficiency_levels (
    level_id,
    code,
    name,
    level_order,
    description,
    evidence_expectations
)
VALUES
(
    gen_random_uuid()::text,
    'awareness',
    'Awareness',
    1,
    'Understands the purpose and basic terminology of the skill.',
    '[
        "Can explain the skill at a high level",
        "Recognizes common terminology",
        "Can identify where the skill is used"
    ]'::json
),
(
    gen_random_uuid()::text,
    'foundational',
    'Foundational',
    2,
    'Can perform basic tasks with guidance and reference material.',
    '[
        "Completes guided exercises",
        "Uses documentation effectively",
        "Understands core concepts"
    ]'::json
),
(
    gen_random_uuid()::text,
    'working',
    'Working Proficiency',
    3,
    'Can apply the skill independently to routine practical work.',
    '[
        "Completes normal tasks independently",
        "Troubleshoots common issues",
        "Can explain implementation choices"
    ]'::json
),
(
    gen_random_uuid()::text,
    'advanced',
    'Advanced',
    4,
    'Can design solutions, handle complex problems, and guide others.',
    '[
        "Designs production-ready solutions",
        "Handles complex edge cases",
        "Reviews and improves other implementations"
    ]'::json
),
(
    gen_random_uuid()::text,
    'expert',
    'Expert',
    5,
    'Demonstrates deep mastery, develops standards, and advances the practice.',
    '[
        "Defines architecture or organizational standards",
        "Solves novel and ambiguous problems",
        "Mentors advanced practitioners",
        "Produces authoritative reusable work"
    ]'::json
)
ON CONFLICT (code) DO NOTHING;