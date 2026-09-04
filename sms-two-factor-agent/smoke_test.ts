import { TwoFactorAgent } from './src/index';

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

console.log('Running smoke test for sms-two-factor-agent...');

// Verify the Agent class is exported and has the expected shape
assert(typeof TwoFactorAgent === 'function', 'TwoFactorAgent must be a class/function');
assert(
  TwoFactorAgent.name === 'TwoFactorAgent',
  `Expected class name 'TwoFactorAgent', got '${TwoFactorAgent.name}'`,
);

// Verify prototype methods exist (Agent SDK contract)
const proto = TwoFactorAgent.prototype;
assert(typeof proto.onRequest === 'function', 'TwoFactorAgent must implement onRequest()');
assert(typeof proto.onScheduled === 'function', 'TwoFactorAgent must implement onScheduled()');

// Verify internal handlers exist
assert(typeof proto.handleSendCode === 'function', 'Missing handleSendCode method');
assert(typeof proto.handleVerifyCode === 'function', 'Missing handleVerifyCode method');

console.log('✅ All smoke test assertions passed. Module loads correctly.');
