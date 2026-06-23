/**
 * Application-wide constants.
 * Single source of truth for contact info, external URLs, and brand strings.
 *
 * STRIPE PAYMENT LINKS
 * Create these in the Stripe Dashboard → Payment Links.
 * Replace the placeholder values with the real links before going live.
 * Format: https://buy.stripe.com/XXXXXXXXXXXXXXXX
 */

export const CONTACT_EMAIL = 'hello@statuteproof.com';
export const TELEGRAM_BASE_URL = 'https://t.me/';

// Stripe Payment Links — replace with real Stripe links before launch
// Leave empty ('') to fall back to the workspace registration flow.
export const STRIPE_LINK_FOUNDING_PILOT = '';   // $199/mo — Founding Pilot
export const STRIPE_LINK_UAE_MONITOR    = '';   // $399/mo — UAE Monitor
