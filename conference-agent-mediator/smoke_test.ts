import { describe, it, expect } from 'vitest';
import { __smoke, ConferenceAgent } from './src/index';

describe('conference-agent-mediator module', () => {
  it('should export the ConferenceAgent class', () => {
    expect(ConferenceAgent).toBeDefined();
    expect(typeof ConferenceAgent).toBe('function');
  });

  it('should export the smoke test helper', () => {
    expect(__smoke).toBeDefined();
    expect(__smoke.ConferenceAgent).toBe(ConferenceAgent);
    expect(typeof __smoke.json).toBe('function');
  });

  it('should instantiate ConferenceAgent with initial state', () => {
    const agent = new ConferenceAgent('agent:test-conf-123', {
      conferenceId: 'test-conf-123',
      callControlId: 'call-ctrl-abc',
      participants: ['alice', 'bob'],
      turns: [],
      lastSpokenAt: {},
      startedAt: Date.now(),
    });

    expect(agent.state.conferenceId).toBe('test-conf-123');
    expect(agent.state.participants).toEqual(['alice', 'bob']);
    expect(agent.state.turns).toEqual([]);
    expect(agent.observers).toBeInstanceOf(Set);
  });

  it('should produce a JSON response from the json helper', () => {
    const res = __smoke.json({ ok: true }, 200);
    expect(res.status).toBe(200);
  });
});
