import { describe, it, expect } from 'vitest'
import { stripeCheckoutUrl } from '../data/constants'

describe('stripeCheckoutUrl — client_reference_id wiring for the Stripe webhook', () => {
  const LINK = 'https://buy.stripe.com/test_abc123'

  it('appends the user id as client_reference_id for a logged-in buyer', () => {
    const url = new URL(stripeCheckoutUrl(LINK, 42))
    expect(url.searchParams.get('client_reference_id')).toBe('42')
    expect(url.origin + url.pathname).toBe('https://buy.stripe.com/test_abc123')
  })

  it('coerces a non-string id to a string', () => {
    expect(new URL(stripeCheckoutUrl(LINK, 7)).searchParams.get('client_reference_id')).toBe('7')
    expect(new URL(stripeCheckoutUrl(LINK, 'usr_9')).searchParams.get('client_reference_id')).toBe('usr_9')
  })

  it('preserves an existing query string on the payment link', () => {
    const url = new URL(stripeCheckoutUrl(LINK + '?prefilled_email=a%40b.com', 5))
    expect(url.searchParams.get('prefilled_email')).toBe('a@b.com')
    expect(url.searchParams.get('client_reference_id')).toBe('5')
  })

  it('returns the link unchanged for an anonymous buyer (no id)', () => {
    expect(stripeCheckoutUrl(LINK, null)).toBe(LINK)
    expect(stripeCheckoutUrl(LINK, undefined)).toBe(LINK)
    expect(stripeCheckoutUrl(LINK, '')).toBe(LINK)
  })

  it('returns the input unchanged for an empty or unparseable link', () => {
    expect(stripeCheckoutUrl('', 5)).toBe('')
    expect(stripeCheckoutUrl('not a url', 5)).toBe('not a url')
  })
})
