/**
 * types/mess.ts — HostelOps AI
 * TypeScript types mirroring backend mess feedback and alert schemas.
 */

export type MealPeriod = 'breakfast' | 'lunch' | 'dinner';

export type MessDimension =
    | 'food_quality'
    | 'food_quantity'
    | 'hygiene'
    | 'menu_variety'
    | 'timing';

export type AlertType = 'chronic' | 'spike';

export interface MessRatings {
    food_quality: number; // 1–5
    food_quantity: number; // 1–5
    hygiene: number; // 1–5
    menu_variety: number; // 1–5
    timing: number; // 1–5
}

export interface MessFeedbackCreate {
    meal: MealPeriod;
    feedback_date: string; // ISO date: YYYY-MM-DD
    food_quality: number;
    food_quantity: number;
    hygiene: number;
    menu_variety: number;
    timing: number;
    comment?: string;
}

export interface MessFeedbackRead {
    id: string;
    student_id: string;
    meal: MealPeriod;
    date: string;
    food_quality: number;
    food_quantity: number;
    hygiene: number;
    menu_variety: number;
    timing: number;
    comment: string | null;
    created_at: string;
}

export interface MessAlertRead {
    id: string;
    alert_type: AlertType;
    dimension: MessDimension;
    meal: MealPeriod;
    triggered_at: string;
    average_score: number;
    participation_count: number;
    resolved: boolean;
    resolved_at: string | null;
}
