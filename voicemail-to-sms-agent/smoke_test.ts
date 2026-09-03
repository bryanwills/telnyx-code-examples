import { VoicemailAgent } from './src/voicemail-agent.ts';

/**
 * Smoke test: verifies that the VoicemailAgent module loads and exports
 * the expected class without runtime errors.
 *
 * Run with: npm test
 */
function runSmokeTest(): void {
  console.log('Running smoke test for VoicemailAgent...');

  if (!VoicemailAgent) {
    throw new Error('VoicemailAgent is undefined');
  }

  const agent = new VoicemailAgent({} as any, {} as any);
  for (const method of ['processVoicemail', 'listVoicemails', 'getStats']) {
    if (typeof (agent as any)[method] !== 'function') {
      throw new Error(`VoicemailAgent is missing method: ${method}`);
    }
  }

  console.log('✅ Smoke test passed: VoicemailAgent loaded with all expected methods.');
}

runSmokeTest();
