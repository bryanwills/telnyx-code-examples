# Telnyx Code Examples — AI Communications Infrastructure

Production-ready code examples for the Telnyx platform. Each example is a self-contained project with working code, documentation, and environment configuration — clone, configure, and run in minutes.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/team-telnyx/telnyx-code-examples.git
cd telnyx-code-examples

# 2. Pick an example
cd send-sms-python

# 3. Configure and run (see each example's README for language-specific commands)
cp .env.example .env
# Edit .env with your Telnyx API key from https://portal.telnyx.com
pip install -r requirements.txt && python app.py
```

> Full API reference at [developers.telnyx.com](https://developers.telnyx.com)

Each example's README has a Quick Start with the exact install/run commands for its language, an `API.md` typed endpoint reference, and a `GUIDE.md` walkthrough.

---

## Voice AI

Build voice applications with [Telnyx Voice AI](https://telnyx.com/products/voice-ai-agents) — IVR menus, call recording, conferencing, WebRTC, and AI-powered call routing.

| Example | Language | Description |
|---------|----------|-------------|
| [route-phone-calls-to-ai-agent-python](./route-phone-calls-to-ai-agent-python/) | Python | Handle inbound calls with webhook-driven AI routing. |
| [make-outbound-phone-call-python](./make-outbound-phone-call-python/) | Python | Initiate outbound calls via the Call Control API. |
| [build-ivr-phone-menu-python](./build-ivr-phone-menu-python/) | Python | Build an interactive voice response menu with DTMF input. |
| [record-phone-calls-python](./record-phone-calls-python/) | Python | Record calls and receive recording webhooks. |
| [transfer-live-phone-calls-python](./transfer-live-phone-calls-python/) | Python | Transfer active calls to another number or agent. |
| [text-to-speech-phone-call-python](./text-to-speech-phone-call-python/) | Python | Play text-to-speech audio during a phone call. |
| [build-conference-calling-python](./build-conference-calling-python/) | Python | Create multi-party conference calls. |
| [call-whisper-monitoring-python](./call-whisper-monitoring-python/) | Python | Monitor calls with whisper prompts for agents. |
| [call-forwarding-python](./call-forwarding-python/) | Python | Forward incoming calls to another destination. |
| [webrtc-browser-calling-python](./webrtc-browser-calling-python/) | Python | Enable browser-based calling with WebRTC. |
| [route-phone-calls-to-ai-agent-nodejs](./route-phone-calls-to-ai-agent-nodejs/) | Node.js | Handle inbound calls with webhook-driven AI routing. |
| [make-outbound-phone-call-nodejs](./make-outbound-phone-call-nodejs/) | Node.js | Initiate outbound calls via the Call Control API. |
| [make-outbound-phone-call-java](./make-outbound-phone-call-java/) | Java | Initiate outbound calls via the Call Control API. |
| [make-outbound-phone-call-csharp](./make-outbound-phone-call-csharp/) | C# | Initiate outbound calls via the Call Control API. |
| [make-outbound-phone-call-ruby](./make-outbound-phone-call-ruby/) | Ruby | Initiate outbound calls via the Call Control API. |
| [build-ivr-phone-menu-nodejs](./build-ivr-phone-menu-nodejs/) | Node.js | Build an interactive voice response menu with DTMF input. |
| [record-phone-calls-nodejs](./record-phone-calls-nodejs/) | Node.js | Record calls and receive recording webhooks. |
| [text-to-speech-phone-call-nodejs](./text-to-speech-phone-call-nodejs/) | Node.js | Play text-to-speech audio during a phone call. |
| [route-phone-calls-to-ai-agent-go](./route-phone-calls-to-ai-agent-go/) | Go | Handle inbound calls with webhook-driven AI routing. |
| [route-phone-calls-to-ai-agent-ruby](./route-phone-calls-to-ai-agent-ruby/) | Ruby | Handle inbound calls with webhook-driven AI routing. |
| [make-outbound-phone-call-php](./make-outbound-phone-call-php/) | PHP | Initiate outbound calls via the Call Control API. |
| [branded-caller-id-manager-python](./branded-caller-id-manager-python/) | Python | Branded Caller ID Manager — register, manage, and verify branded calling profiles with STIR/SHAKEN attestation for higher answer rates. |
| [bulk-number-validation-cleaner-python](./bulk-number-validation-cleaner-python/) | Python | Bulk Number Validation & Cleaner — validate and clean phone number lists via Telnyx Number Lookup API. |
| [call-analytics-dashboard-api-python](./call-analytics-dashboard-api-python/) | Python | SMS application. Built with Telnyx CDR, Migration, Number Porting, SMS/MMS. |
| [call-queue-with-hold-music-python](./call-queue-with-hold-music-python/) | Python | Call Queue with Hold Music — queue callers with position announcements and hold music, route to agents. |
| [call-sentiment-live-escalation-python](./call-sentiment-live-escalation-python/) | Python | Call Sentiment Live Escalation — monitor call transcripts in real-time. When negative sentiment or distress is detected, auto-escalate to a supervisor. |
| [call-whisper-screen-pop-python](./call-whisper-screen-pop-python/) | Python | Call Whisper & Screen Pop — whisper caller info to agent before connecting the call. |
| [cloud-storage-call-archive-python](./cloud-storage-call-archive-python/) | Python | Cloud Storage Call Archive — archive call recordings to Telnyx Cloud Storage (S3-compatible) with searchable metadata. |
| [cnam-caller-id-lookup-enrichment-python](./cnam-caller-id-lookup-enrichment-python/) | Python | CNAM Caller ID Lookup Enrichment — look up CNAM for inbound callers, enrich CRM records with caller identity. |
| [commercial-voiceover-generator-python](./commercial-voiceover-generator-python/) | Python | Provide product name, target audience, and tone. AI writes 3 script variations with timing marks, TTS renders each in multiple voices, delivers top picks via SMS for client approval. |
| [conference-live-poll-dtmf-python](./conference-live-poll-dtmf-python/) | Python | Conference Live Poll via DTMF — host asks a question, all conference participants vote by pressing 1-4, results tallied instantly. |
| [deepfake-voice-detector-python](./deepfake-voice-detector-python/) | Python | Real-time synthetic speech detection on live phone calls. Captures audio via media streaming, extracts acoustic features, scores deepfake probability with AI Inference, alerts security team via Slack. |
| [fax-to-structured-data-pipeline-python](./fax-to-structured-data-pipeline-python/) | Python | Fax-to-Structured-Data Pipeline — receive faxes, AI extracts structured data (invoices, orders, prescriptions) into JSON. |
| [live-podcast-call-in-python](./live-podcast-call-in-python/) | Python | Hosts on a conference call, listeners call in. AI screens callers via STT, queues approved ones, generates real-time fact-checks for the host, TTS announces topics. |
| [media-stream-voice-cloak-python](./media-stream-voice-cloak-python/) | Python | Media Stream Voice Cloak — real-time voice modification via media streaming API. Apply pitch shift, echo, or anonymization. |
| [multi-number-identity-router-python](./multi-number-identity-router-python/) | Python | Multi-Number Identity Router — route calls based on which number was dialed. Each number maps to a different business identity, greeting, and routing destination. |
| [multilingual-voiceover-kit-python](./multilingual-voiceover-kit-python/) | Python | Submit a script in one language, AI translates to multiple targets preserving tone and timing, TTS renders each language with native-sounding voices. Batch localization for 15 languages. |
| [number-lookup-fraud-screener-python](./number-lookup-fraud-screener-python/) | Python | Number Lookup Fraud Screener — screen inbound calls/messages for fraud indicators using number lookup before connecting. |
| [number-lookup-lead-enrichment-python](./number-lookup-lead-enrichment-python/) | Python | Number Lookup Lead Enrichment — CNAM and carrier lookup to qualify and enrich sales leads. |
| [number-porting-status-tracker-python](./number-porting-status-tracker-python/) | Python | Number Porting Status Tracker — track porting orders with status webhooks and SMS alerts. |
| [number-reputation-monitor-auto-rotate-python](./number-reputation-monitor-auto-rotate-python/) | Python | Number Reputation Monitor — track outbound number reputation, auto-rotate flagged numbers. |
| [number-search-and-purchase-api-python](./number-search-and-purchase-api-python/) | Python | Number Search and Purchase API — search, filter, and buy phone numbers programmatically. |
| [number-warmup-reputation-builder-python](./number-warmup-reputation-builder-python/) | Python | Number Warmup & Reputation Builder — gradually ramp SMS volume on new numbers to build carrier reputation and avoid spam flags. |
| [porting-loa-automation-python](./porting-loa-automation-python/) | Python | Porting LOA Automation — automate Letter of Authorization generation and porting order submission. |
| [porting-order-tracker-dashboard-python](./porting-order-tracker-dashboard-python/) | Python | Porting Order Tracker Dashboard â submit, track, and manage porting orders with SLA monitoring, timeline visualization, and bulk operations. |
| [real-time-call-intelligence-dashboard-python](./real-time-call-intelligence-dashboard-python/) | Python | Real-Time Call Intelligence Dashboard — live transcription, sentiment analysis, and competitor detection. |
| [smart-number-geo-assignment-python](./smart-number-geo-assignment-python/) | Python | Smart Number Geo-Assignment — automatically purchase and assign local numbers based on caller geography to maximize answer rates. |
| [texml-dynamic-call-router-python](./texml-dynamic-call-router-python/) | Python | TeXML Dynamic Call Router — time-of-day and caller-based routing with TeXML responses. |
| [video-voiceover-replacement-python](./video-voiceover-replacement-python/) | Python | Upload audio with existing voice-over. STT extracts the script, AI rewrites/improves it (5 modes: polish, professional, simplify, energize, shorten), TTS re-records with studio quality. |
| [video-webinar-recording-manager-python](./video-webinar-recording-manager-python/) | Python | Video Webinar Recording Manager — manage video room webinars with automatic recording, transcription, and clip extraction. |
| [voice-to-slack-bridge-python](./voice-to-slack-bridge-python/) | Python | Voice-to-Slack Bridge — call a phone number, speak a message, AI transcribes and posts to Slack with urgency tagging. |
| [voice-verified-identity-2fa-python](./voice-verified-identity-2fa-python/) | Python | Voice-Verified Identity + 2FA — Number Lookup, SMS OTP, and AI-assisted secure transactions. |
| [voiceover-audition-generator-python](./voiceover-audition-generator-python/) | Python | Submit a script, hear it read by every available TTS voice. AI scores and ranks best-fit voices based on content, tone, and audience. SMS delivers top picks to decision-makers. |
| [wireguard-private-voice-network-python](./wireguard-private-voice-network-python/) | Python | WireGuard Private Voice Network — create WireGuard mesh network for private SIP trunking with encrypted voice traffic. |

## SMS & MMS

Send and receive text messages with the [Telnyx SMS API](https://telnyx.com/products/sms-api) — build autoresponders, implement 2FA, and manage bulk messaging campaigns.

| Example | Language | Description |
|---------|----------|-------------|
| [send-sms-python](./send-sms-python/) | Python | Send a single SMS message via the Telnyx API. |
| [receive-sms-webhook-python](./receive-sms-webhook-python/) | Python | Receive inbound SMS via webhook. |
| [send-bulk-sms-python](./send-bulk-sms-python/) | Python | Send SMS messages to multiple recipients. |
| [sms-two-factor-auth-python](./sms-two-factor-auth-python/) | Python | Implement SMS-based two-factor authentication. |
| [send-mms-picture-message-python](./send-mms-picture-message-python/) | Python | Send MMS messages with media attachments. |
| [sms-auto-reply-bot-python](./sms-auto-reply-bot-python/) | Python | Build an SMS autoresponder bot. |
| [send-sms-nodejs](./send-sms-nodejs/) | Node.js | Send a single SMS message via the Telnyx API. |
| [receive-sms-webhook-nodejs](./receive-sms-webhook-nodejs/) | Node.js | Receive inbound SMS via webhook. |
| [receive-sms-webhook-csharp](./receive-sms-webhook-csharp/) | C# | Receive inbound SMS via webhook (Ed25519-verified). |
| [sms-two-factor-auth-nodejs](./sms-two-factor-auth-nodejs/) | Node.js | Implement SMS-based two-factor authentication. |
| [send-bulk-sms-nodejs](./send-bulk-sms-nodejs/) | Node.js | Send SMS messages to multiple recipients. |
| [receive-sms-webhook-java](./receive-sms-webhook-java/) | Java | Receive inbound SMS via webhook with Ed25519 signature verification. |
| [receive-sms-webhook-php](./receive-sms-webhook-php/) | PHP | Receive inbound SMS via webhook with Ed25519 signature verification. |
| [receive-sms-webhook-ruby](./receive-sms-webhook-ruby/) | Ruby | Receive inbound SMS via webhook with Ed25519 signature verification. |
| [send-sms-go](./send-sms-go/) | Go | Send a single SMS message via the Telnyx API. |
| [send-sms-ruby](./send-sms-ruby/) | Ruby | Send a single SMS message via the Telnyx API. |
| [send-sms-csharp](./send-sms-csharp/) | C# | Send a single SMS message via the Telnyx API. |
| [send-sms-java](./send-sms-java/) | Java | Send a single SMS message via the Telnyx API. |
| [send-sms-php](./send-sms-php/) | PHP | Send a single SMS message via the Telnyx API. |
| [abandoned-cart-recovery-python](./abandoned-cart-recovery-python/) | Python | SMS 1h after abandon with incentive, AI voice call 24h later if no purchase. Integrates with Shopify webhooks and Stripe for discount codes. |
| [accounting-tax-season-line-python](./accounting-tax-season-line-python/) | Python | Handles scheduling, document checklist reminders, status updates. AI texts clients with missing doc reminders. CPA reviews readiness before appointments. |
| [after-hours-nurse-triage-python](./after-hours-nurse-triage-python/) | Python | AI screens symptoms using clinical decision tree, routes urgent to on-call nurse via PagerDuty, queues non-urgent for AM callback. Nurse reviews and overrides AI severity scores. |
| [ai-appointment-booking-sms-flow-python](./ai-appointment-booking-sms-flow-python/) | Python | AI Appointment Booking SMS Flow — guided SMS booking with available slot selection. |
| [ai-appointment-reminder-sms-voice-python](./ai-appointment-reminder-sms-voice-python/) | Python | AI Appointment Reminder — SMS first, voice call for non-responders, AI handles rescheduling. |
| [autonomous-outbound-sales-agent-python](./autonomous-outbound-sales-agent-python/) | Python | Autonomous Outbound Sales Agent — AI-driven lead qualification, objection handling, and meeting booking. |
| [billing-anomaly-detector-python](./billing-anomaly-detector-python/) | Python | Billing Anomaly Detector — monitor usage and billing for anomalies, alert on cost spikes and unusual patterns. |
| [cdr-usage-analytics-dashboard-python](./cdr-usage-analytics-dashboard-python/) | Python | Pull Call Detail Records, build usage analytics with cost breakdowns, peak-hour analysis, and AI-powered insights. |
| [cloud-storage-media-cdn-python](./cloud-storage-media-cdn-python/) | Python | Cloud Storage Media CDN — use Telnyx Cloud Storage (S3-compatible) as a CDN for IVR prompts, hold music, and voice assets. |
| [e911-address-validator-python](./e911-address-validator-python/) | Python | Application. Built with Telnyx E911, Migration, Number Porting. |
| [ecommerce-order-status-bot-python](./ecommerce-order-status-bot-python/) | Python | Customers call or text order number, get real-time Shopify tracking. AI detects delivery exceptions and proactively texts customers before they call support. |
| [edge-compute-webhook-proxy-python](./edge-compute-webhook-proxy-python/) | Python | Receive Telnyx voice and SMS webhooks at the edge with minimal latency. Validates, enriches with timestamps, HMAC-signs, and forwards to your backend. |
| [edge-mcp-server-deploy-python](./edge-mcp-server-deploy-python/) | Python | Deploy an MCP server to Telnyx Edge Compute exposing Telnyx APIs as tools for AI agents. Send SMS, search numbers, run inference. |
| [elearning-course-narrator-python](./elearning-course-narrator-python/) | Python | Upload course content, AI structures into audio modules with pacing cues and quiz prompts, TTS narrates each module, stores in Cloud Storage with a JSON manifest. |
| [emergency-mass-notification-system-python](./emergency-mass-notification-system-python/) | Python | Emergency Mass Notification System — SMS + voice calls with delivery tracking and escalation. |
| [fraud-alert-verification-python](./fraud-alert-verification-python/) | Python | Suspicious transaction triggers voice call to customer, verifies via DTMF, blocks or approves in real-time. Fraud team reviews edge cases via Slack. |
| [global-lead-response-engine-python](./global-lead-response-engine-python/) | Python | Global Lead Response Engine — multi-language AI qualification with live transfer and omnichannel follow-up. |
| [hosted-messaging-campaign-manager-python](./hosted-messaging-campaign-manager-python/) | Python | Hosted Messaging Campaign Manager — manage hosted messaging campaigns with subscriber opt-in/out tracking and delivery analytics. |
| [hotel-guest-services-python](./hotel-guest-services-python/) | Python | Room service, housekeeping, concierge requests via voice or SMS. AI routes and tracks. Staff gets Slack notifications, guest gets SMS when fulfilled. |
| [interview-screen-scheduler-python](./interview-screen-scheduler-python/) | Python | Candidate applies, AI calls for 5-min phone screen, scores answers, books qualified candidates on hiring manager's calendar. Integrates with Greenhouse ATS and Google Calendar. |
| [isv-notification-engine-python](./isv-notification-engine-python/) | Python | SaaS platform sends alerts via SMS/voice/WhatsApp based on customer preference and urgency. Multi-channel with fallback cascade and delivery tracking. |
| [ivr-prompt-generator-python](./ivr-prompt-generator-python/) | Python | Generate professional IVR/phone system prompts. AI writes caller-friendly scripts from business descriptions, TTS renders in multiple voices, test via live Telnyx call playback. |
| [law-firm-client-intake-python](./law-firm-client-intake-python/) | Python | AI answers after-hours calls, screens case type, collects facts, runs conflict check, books consultation via Calendly, collects retainer deposit via Stripe. |
| [marketplace-comms-bridge-python](./marketplace-comms-bridge-python/) | Python | Buyer texts about a listing, AI responds with details, facilitates anonymous buyer-seller connection via masked numbers, handles scheduling. Ops reviews flagged conversations. |
| [media-stream-custom-audio-mixer-python](./media-stream-custom-audio-mixer-python/) | Python | Media Stream Custom Audio Mixer — mix custom audio into live calls via WebSocket-based media streaming. |
| [media-stream-live-transcription-python](./media-stream-live-transcription-python/) | Python | Media Stream Live Transcription — fork call audio to WebSocket for real-time transcription display. |
| [messaging-campaign-ab-test-optimizer-python](./messaging-campaign-ab-test-optimizer-python/) | Python | Messaging Campaign A/B Test Optimizer — test SMS copy variants, AI picks winners, auto-scales. |
| [migrate-from-elevenlabs-python](./migrate-from-elevenlabs-python/) | Python | Migrate from ElevenLabs — import ElevenLabs voice configurations to Telnyx TTS with voice mapping and cost comparison. |
| [migrate-from-twilio-python](./migrate-from-twilio-python/) | Python | Migrate from Twilio — complete Twilio-to-Telnyx migration tool: numbers, messaging profiles, voice apps, and webhook configs. |
| [migrate-from-vapi-python](./migrate-from-vapi-python/) | Python | Migrate from Vapi — import Vapi voice agents to Telnyx AI Assistants with voice, prompt, and tool configuration mapping. |
| [missions-workflow-orchestrator-python](./missions-workflow-orchestrator-python/) | Python | Missions Workflow Orchestrator — create and manage multi-step mission workflows using the Telnyx Missions API. |
| [mms-photo-inventory-tracker-python](./mms-photo-inventory-tracker-python/) | Python | MMS Photo Inventory Tracker — text a photo of inventory items with MMS, AI identifies and catalogs them automatically. |
| [mms-receipt-scanner-expense-tracker-python](./mms-receipt-scanner-expense-tracker-python/) | Python | MMS Receipt Scanner & Expense Tracker — text a photo of a receipt, AI extracts data and tracks expenses. |
| [multi-channel-appointment-confirmation-python](./multi-channel-appointment-confirmation-python/) | Python | Multi-Channel Appointment Confirmation — confirm appointments via SMS, voice call, and WhatsApp. Tries SMS first, escalates to voice if no response. |
| [multi-language-customer-survey-python](./multi-language-customer-survey-python/) | Python | Multi-Language Customer Survey — outbound voice surveys in the caller's language with AI analysis. |
| [patient-appointment-engine-python](./patient-appointment-engine-python/) | Python | AI answers calls, checks availability, books appointments, collects copay via Stripe, sends SMS confirmation. Staff reviews next-day schedule. |
| [payment-reminder-escalation-python](./payment-reminder-escalation-python/) | Python | Invoice overdue: day 1 SMS, day 7 voice call with payment link, day 14 escalation to collections with full context. Integrates with Stripe/QuickBooks. |
| [podcast-episode-repurposer-python](./podcast-episode-repurposer-python/) | Python | Upload a recorded episode, STT transcribes, AI Inference extracts key quotes and topics, TTS generates audiogram clips with different voices, SMS distributes clips to subscribers. |
| [podcast-highlight-clipper-python](./podcast-highlight-clipper-python/) | Python | Upload audio, STT + AI Inference identifies viral moments with virality scoring, TTS generates teaser intros for each clip, SMS distributes highlights to subscriber list. |
| [post-service-followup-engine-python](./post-service-followup-engine-python/) | Python | After appointment, SMS satisfaction survey. Negative responses trigger AI voice callback to understand the issue, then creates ticket in Jira and alerts manager via Slack. |
| [prescription-refill-line-python](./prescription-refill-line-python/) | Python | Patient calls, AI verifies identity (DOB + last 4 of phone), checks refill eligibility, sends approval to pharmacist via Slack. Pharmacist approves/denies, patient gets SMS. |
| [programmable-hold-experience-python](./programmable-hold-experience-python/) | Python | Programmable Hold Experience — custom hold experiences: tips, trivia, estimated wait time, callback offers. |
| [rcs-rich-card-product-catalog-python](./rcs-rich-card-product-catalog-python/) | Python | RCS Rich Card Product Catalog — AI-powered product recommendations with rich cards and carousels. |
| [rent-collection-escalation-python](./rent-collection-escalation-python/) | Python | Automated multi-channel rent reminders. Day 1: SMS + Stripe payment link. Day 3: voice call. Day 7: late fee notice. Day 14: manager escalation. |
| [returns-processor-python](./returns-processor-python/) | Python | Customer texts photo of defective item via MMS, AI evaluates damage, auto-approves low-value refunds via Stripe, escalates high-value to team lead. |
| [service-booking-dispatch-python](./service-booking-dispatch-python/) | Python | Customer calls HVAC/plumber/electrician, AI checks tech availability, books slot, collects deposit via Stripe, texts confirmation to customer and tech. |
| [shift-fill-engine-python](./shift-fill-engine-python/) | Python | Open shift triggers calls down the availability list. First to confirm gets it, rest are cancelled. Texts confirmation + notifies manager via Slack. |
| [smart-ivr-ab-tester-python](./smart-ivr-ab-tester-python/) | Python | Smart IVR A/B Tester — run two IVR flows simultaneously and track which converts better. |
| [sms-appointment-no-show-predictor-python](./sms-appointment-no-show-predictor-python/) | Python | SMS Appointment No-Show Predictor — AI predicts no-shows from SMS response patterns, triggers interventions. |
| [sms-chatbot-with-conversation-memory-python](./sms-chatbot-with-conversation-memory-python/) | Python | SMS Chatbot with Conversation Memory — persistent AI conversations over text with context retention. |
| [sms-drip-campaign-engine-python](./sms-drip-campaign-engine-python/) | Python | SMS Drip Campaign Engine — multi-step nurture sequences with branch logic and AI personalization. |
| [sms-emergency-check-in-python](./sms-emergency-check-in-python/) | Python | SMS Emergency Check-In — periodic wellness checks via SMS with escalation to emergency contacts. |
| [sms-escape-room-game-python](./sms-escape-room-game-python/) | Python | SMS Escape Room Game — text-based adventure game over SMS. Solve puzzles, find clues, escape before time runs out. |
| [sms-keyword-auto-responder-python](./sms-keyword-auto-responder-python/) | Python | SMS Keyword Auto-Responder — keyword-triggered responses with match analytics. |
| [sms-poll-voting-system-python](./sms-poll-voting-system-python/) | Python | SMS Poll Voting System — text-to-vote polling with real-time results. |
| [sms-trivia-game-tournament-python](./sms-trivia-game-tournament-python/) | Python | SMS Trivia Game Tournament — multi-player trivia via SMS. Players join, answer timed questions, scores tracked on a live leaderboard. |
| [toll-free-sms-campaign-manager-python](./toll-free-sms-campaign-manager-python/) | Python | Toll-Free SMS Campaign Manager — manage toll-free verification and send compliant campaigns. |
| [verify-multi-channel-auth-python](./verify-multi-channel-auth-python/) | Python | Verify Multi-Channel Auth — multi-channel verification: SMS first, fallback to voice call, then WhatsApp. Cascading 2FA. |
| [verify-phone-number-otp-flow-python](./verify-phone-number-otp-flow-python/) | Python | Verify Phone Number OTP Flow — Telnyx Verify API with SMS primary and voice call fallback. |
| [whatsapp-order-tracking-notifications-python](./whatsapp-order-tracking-notifications-python/) | Python | WhatsApp Order Tracking Notifications — proactive shipping updates and AI-powered order inquiries. |
| [whatsapp-sms-bridge-python](./whatsapp-sms-bridge-python/) | Python | WhatsApp-SMS Bridge — receive messages on WhatsApp and forward them via SMS, and vice versa. Bidirectional bridge between two messaging channels. |
| [white-label-appointment-platform-python](./white-label-appointment-platform-python/) | Python | Multi-tenant SaaS that gives any service business their own AI phone line with booking, reminders, and calendar sync. Each tenant has own number, greeting, and config. |
| [x402-usdc-account-funder-python](./x402-usdc-account-funder-python/) | Python | X402 USDC Account Funder — fund your Telnyx account with USDC cryptocurrency on the Base blockchain. |
| [two-way-sms-chat-python](./two-way-sms-chat-python/) | Python | pip install -r requirements.txt. |
| [sms-survey-bot-python](./sms-survey-bot-python/) | Python | pip install -r requirements.txt. |
| [schedule-sms-messages-python](./schedule-sms-messages-python/) | Python | pip install -r requirements.txt. |
| [alphanumeric-sender-id-sms-python](./alphanumeric-sender-id-sms-python/) | Python | pip install -r requirements.txt. |
| [long-code-sms-python](./long-code-sms-python/) | Python | pip install -r requirements.txt. |
| [toll-free-sms-python](./toll-free-sms-python/) | Python | pip install -r requirements.txt. |
| [shortcode-sms-python](./shortcode-sms-python/) | Python | pip install -r requirements.txt. |
| [receive-mms-webhook-python](./receive-mms-webhook-python/) | Python | pip install -r requirements.txt. |
| [sms-delivery-receipts-python](./sms-delivery-receipts-python/) | Python | pip install -r requirements.txt. |
| [phone-number-lookup-python](./phone-number-lookup-python/) | Python | pip install -r requirements.txt. |
| [sms-opt-out-management-python](./sms-opt-out-management-python/) | Python | pip install -r requirements.txt. |
| [sms-conversation-threading-python](./sms-conversation-threading-python/) | Python | pip install -r requirements.txt. |
| [send-sms-notifications-python](./send-sms-notifications-python/) | Python | pip install -r requirements.txt. |
| [sms-marketing-campaign-python](./sms-marketing-campaign-python/) | Python | pip install -r requirements.txt. |
| [two-way-sms-chat-nodejs](./two-way-sms-chat-nodejs/) | Node.js | npm install. |
| [send-mms-picture-message-nodejs](./send-mms-picture-message-nodejs/) | Node.js | npm install. |
| [sms-auto-reply-bot-nodejs](./sms-auto-reply-bot-nodejs/) | Node.js | npm install. |
| [sms-delivery-receipts-nodejs](./sms-delivery-receipts-nodejs/) | Node.js | npm install. |

## AI Assistants

Create, manage, and chat with [Telnyx AI Assistants](https://telnyx.com/ai-assistants) — LLM-powered agents for voice and messaging automation.

| Example | Language | Description |
|---------|----------|-------------|
| [create-ai-assistant-python](./create-ai-assistant-python/) | Python | Create a new AI assistant with custom instructions. |
| [chat-with-ai-assistant-python](./chat-with-ai-assistant-python/) | Python | Send messages to an AI assistant and receive responses. |
| [list-ai-assistants-python](./list-ai-assistants-python/) | Python | List and manage your AI assistants. |
| [clone-ai-assistant-python](./clone-ai-assistant-python/) | Python | Clone an existing AI assistant configuration. |
| [update-ai-assistant-python](./update-ai-assistant-python/) | Python | Update an AI assistant's instructions and settings. |
| [create-ai-assistant-nodejs](./create-ai-assistant-nodejs/) | Node.js | Create a new AI assistant with custom instructions. |
| [chat-with-ai-assistant-nodejs](./chat-with-ai-assistant-nodejs/) | Node.js | Send messages to an AI assistant and receive responses. |
| [chat-with-ai-assistant-php](./chat-with-ai-assistant-php/) | PHP | Send messages to an AI assistant and receive responses, keeping conversation context. |
| [list-ai-assistants-nodejs](./list-ai-assistants-nodejs/) | Node.js | List and manage your AI assistants. |
| [chat-with-ai-assistant-java](./chat-with-ai-assistant-java/) | Java | Send messages to an AI assistant and thread a multi-turn conversation. |
| [chat-with-ai-assistant-ruby](./chat-with-ai-assistant-ruby/) | Ruby | Chat with an AI assistant and maintain conversation context via a Sinatra endpoint. |
| [chat-with-ai-assistant-go](./chat-with-ai-assistant-go/) | Go | Send messages to an AI assistant and maintain multi-turn context with a conversation id via a Gin endpoint. |
| [ai-after-hours-emergency-triage-python](./ai-after-hours-emergency-triage-python/) | Python | AI After-Hours Emergency Triage — after-hours calls screened by AI. True emergencies get forwarded to on-call; everything else gets a voicemail + next-day callback promise. |
| [ai-assistant-knowledge-base-python](./ai-assistant-knowledge-base-python/) | Python | AI Assistant Knowledge Base — AI Assistant with document knowledge base for context-aware Q&A over uploaded documents. |
| [ai-assistant-multi-tool-python](./ai-assistant-multi-tool-python/) | Python | AI Assistant Multi-Tool — AI Assistant with custom function-calling tools for CRM lookup, appointment booking, and order status. |
| [ai-assistant-phone-setup-python](./ai-assistant-phone-setup-python/) | Python | AI Assistant Phone Setup — create and configure a managed Telnyx AI Assistant and wire it to a phone number. |
| [ai-audiobook-narrator-python](./ai-audiobook-narrator-python/) | Python | Submit text, AI Inference chunks into chapters with pacing/emotion markup, TTS narrates each chapter with consistent voice, stores final audio in Telnyx Cloud Storage. |
| [ai-billing-dispute-resolution-agent-python](./ai-billing-dispute-resolution-agent-python/) | Python | AI Billing Dispute Resolution Agent — handles billing questions with account lookup. |
| [ai-call-center-quality-scorer-python](./ai-call-center-quality-scorer-python/) | Python | AI Call Center Quality Scorer — automatically score agent performance from call recordings on compliance, empathy, resolution, and talk-to-listen ratio. |
| [ai-cold-caller-objection-trainer-python](./ai-cold-caller-objection-trainer-python/) | Python | AI Cold Caller Objection Trainer — practice handling sales objections with AI-generated scenarios. |
| [ai-competitive-win-loss-call-analyzer-python](./ai-competitive-win-loss-call-analyzer-python/) | Python | AI Competitive Win/Loss Call Analyzer — analyze recorded sales calls for competitive intelligence. |
| [ai-compliance-quiz-phone-python](./ai-compliance-quiz-phone-python/) | Python | AI Compliance Quiz Phone — employees call and take a compliance quiz. AI asks questions, evaluates answers, scores pass/fail, records completion. |
| [ai-conference-moderator-python](./ai-conference-moderator-python/) | Python | AI moderator for multi-party calls. Manages agenda, enforces time limits, tracks speakers, produces structured summary with action items. |
| [ai-conference-note-taker-python](./ai-conference-note-taker-python/) | Python | AI Conference Note-Taker — joins calls, transcribes, extracts action items, sends SMS summaries. |
| [ai-content-translator-python](./ai-content-translator-python/) | Python | Upload any audio (podcast, meeting, lecture), STT transcribes in source language, AI Inference translates, TTS generates audio in target language. Returns translated audio + aligned transcript. |
| [ai-customer-churn-predictor-python](./ai-customer-churn-predictor-python/) | Python | AI Customer Churn Predictor — analyze call/message patterns via Telnyx APIs, AI predicts churn risk and suggests interventions. |
| [ai-customer-winback-caller-python](./ai-customer-winback-caller-python/) | Python | AI Customer Winback Caller — AI calls churned customers with personalized re-engagement offers. |
| [ai-debt-collection-compliance-agent-python](./ai-debt-collection-compliance-agent-python/) | Python | AI Debt Collection Compliance Agent — FDCPA-compliant outbound collection with real-time guardrails. |
| [ai-deposition-assistant-python](./ai-deposition-assistant-python/) | Python | AI joins legal deposition calls, produces real-time transcript, flags objectionable questions, tracks exhibits, generates structured deposition summary. |
| [ai-event-rsvp-phone-line-python](./ai-event-rsvp-phone-line-python/) | Python | AI Event RSVP Phone Line — call to RSVP for an event. AI collects guest info, dietary restrictions, plus-ones, and confirms the reservation. |
| [ai-hiring-phone-screen-python](./ai-hiring-phone-screen-python/) | Python | AI Hiring Phone Screen — automated first-round phone screening for job applicants. |
| [ai-insurance-claims-intake-voice-python](./ai-insurance-claims-intake-voice-python/) | Python | AI Insurance Claims Intake — voice agent collects claim details, classifies, routes to adjuster. |
| [ai-language-learning-phone-tutor-python](./ai-language-learning-phone-tutor-python/) | Python | AI Language Learning Phone Tutor — call a number, practice a foreign language with AI. |
| [ai-live-call-participant-python](./ai-live-call-participant-python/) | Python | AI joins a live multi-human conference call as an active participant. Listens via media streaming, contributes via TTS, takes notes, responds when addressed by name. |
| [ai-medical-appointment-prep-caller-python](./ai-medical-appointment-prep-caller-python/) | Python | AI Medical Appointment Prep Caller — calls patients before appointments to collect intake info. |
| [ai-meeting-action-tracker-python](./ai-meeting-action-tracker-python/) | Python | Joins multi-party calls, identifies speakers, extracts action items with owners and deadlines, posts structured notes to Slack. |
| [ai-negotiation-practice-phone-python](./ai-negotiation-practice-phone-python/) | Python | AI Negotiation Practice Phone — practice salary negotiations, sales deals, or vendor contracts with an AI that plays the opposing side and scores your technique. |
| [ai-phone-story-hotline-python](./ai-phone-story-hotline-python/) | Python | AI Phone Story Hotline — call a number, choose a genre, and listen to an AI-generated interactive story where your choices shape the narrative. |
| [ai-phone-tree-builder-from-description-python](./ai-phone-tree-builder-from-description-python/) | Python | AI Phone Tree Builder — describe your business in English, AI creates a working phone system. |
| [ai-podcast-call-in-show-python](./ai-podcast-call-in-show-python/) | Python | AI Podcast Call-In Show — callers dial in, AI screens and queues them, host manages live. |
| [ai-podcast-post-producer-python](./ai-podcast-post-producer-python/) | Python | AI Podcast Post-Producer — record a podcast over a conference call, then AI generates show notes, timestamps, highlights, and social media clips. |
| [ai-podcast-producer-python](./ai-podcast-producer-python/) | Python | Record a multi-host podcast via conference call, transcribe each speaker with STT, generate show notes + chapters + social clips via AI Inference, and produce TTS intro/outro bumpers. |
| [ai-powered-ivr-replacement-python](./ai-powered-ivr-replacement-python/) | Python | AI-Powered IVR Replacement — natural language routing with A/B testing and structured insights. |
| [ai-price-quote-phone-agent-python](./ai-price-quote-phone-agent-python/) | Python | AI Price Quote Phone Agent — caller describes what they need, AI generates a customized price quote in real time with line items. |
| [ai-property-management-maintenance-line-python](./ai-property-management-maintenance-line-python/) | Python | AI Property Management Maintenance Line — tenants call, AI triages maintenance requests. |
| [ai-real-estate-showing-scheduler-python](./ai-real-estate-showing-scheduler-python/) | Python | AI Real Estate Showing Scheduler — buyers call or text, AI checks availability and books showings. |
| [ai-real-time-translation-bridge-python](./ai-real-time-translation-bridge-python/) | Python | Connect two callers who speak different languages with real-time AI translation on a live phone call. Built with Telnyx Voice Call Control and AI Inference. |
| [ai-receptionist-with-booking-tools-python](./ai-receptionist-with-booking-tools-python/) | Python | AI Receptionist with Booking Tools — AI Assistant with tool_use for real calendar booking actions. |
| [ai-restaurant-reservation-voice-agent-python](./ai-restaurant-reservation-voice-agent-python/) | Python | AI Restaurant Reservation Voice Agent — handles calls, checks availability, books tables, sends SMS confirmation. |
| [ai-sales-call-with-live-crm-updates-python](./ai-sales-call-with-live-crm-updates-python/) | Python | AI Sales Call with Live CRM Updates — multi-participant call with real-time deal intelligence. |
| [ai-sales-coach-whisper-python](./ai-sales-coach-whisper-python/) | Python | AI coach listens to a live sales call and whispers real-time suggestions to the rep only. Customer never hears the AI. Generates post-call scorecard. |
| [ai-sales-demo-booking-agent-python](./ai-sales-demo-booking-agent-python/) | Python | AI Sales Demo Booking Agent — inbound calls, AI qualifies the lead, books a demo on the calendar. |
| [ai-standup-facilitator-phone-python](./ai-standup-facilitator-phone-python/) | Python | AI Standup Facilitator Phone — team members call in their daily standup update. AI collects what they did, what they're doing, and blockers, then summarizes for the team. |
| [ai-tech-support-voice-agent-python](./ai-tech-support-voice-agent-python/) | Python | Voice application powered by Telnyx AI Inference. Built with Telnyx AI Assistants, AI Inference, Migration, Number Porting. |
| [ai-video-dubbing-pipeline-python](./ai-video-dubbing-pipeline-python/) | Python | Upload audio, STT transcribes with speaker diarization, AI Inference translates to target language, TTS generates dubbed audio with speaker-matched voices. Full STT-to-TTS pipeline. |
| [ai-voice-agent-with-function-calling-python](./ai-voice-agent-with-function-calling-python/) | Python | AI Voice Agent with Function Calling — voice agent that calls external APIs mid-conversation. |
| [ai-voice-memo-to-email-python](./ai-voice-memo-to-email-python/) | Python | AI Voice Memo to Email — call a number, dictate a memo, AI cleans it up and sends it as a formatted email via Telnyx. |
| [ai-voice-survey-sentiment-tracker-python](./ai-voice-survey-sentiment-tracker-python/) | Python | AI Voice Survey Sentiment Tracker — real-time CSAT scoring from voice tone and word choice. |
| [ai-voicemail-transcription-forwarding-python](./ai-voicemail-transcription-forwarding-python/) | Python | AI Voicemail Transcription & Forwarding — voicemail to AI-summarized SMS/email with priority classification. |
| [ai-voiceover-studio-python](./ai-voiceover-studio-python/) | Python | Upload a script, select voice/style/pacing, AI adds professional direction cues (pauses, emphasis, pacing), TTS renders the voice-over, stores output in Cloud Storage. Supports multiple takes and retakes. |
| [build-voice-ai-agent-nodejs](./build-voice-ai-agent-nodejs/) | Node.js | npm install. |
| [build-voice-ai-agent-python](./build-voice-ai-agent-python/) | Python | Build a complete voice AI agent with Telnyx — inbound call handling, AI conversation, and call control. |
| [call-recording-ai-summarizer-python](./call-recording-ai-summarizer-python/) | Python | Call Recording AI Summarizer — record calls, then summarize and extract action items with AI. |
| [click-to-call-webrtc-with-ai-assist-python](./click-to-call-webrtc-with-ai-assist-python/) | Python | Click-to-Call WebRTC with AI Assist — browser-based calling with real-time AI coaching sidebar. |
| [compliance-call-recorder-ai-auditor-python](./compliance-call-recorder-ai-auditor-python/) | Python | Compliance Call Recorder + AI Auditor — auto-record, batch-process with AI, flag violations, create tickets. |
| [conference-call-with-ai-summary-python](./conference-call-with-ai-summary-python/) | Python | Conference Call with AI Summary — multi-party conference with transcription and AI post-call summary. |
| [fax-to-ai-document-processor-python](./fax-to-ai-document-processor-python/) | Python | Fax to AI Document Processor — receive fax, AI extracts data, forwards structured summary. |
| [full-stack-ai-contact-center-python](./full-stack-ai-contact-center-python/) | Python | Full-Stack AI Contact Center — complete contact center: IVR + queue + AI agent assist + recording + live analytics. |
| [global-ip-failover-monitor-python](./global-ip-failover-monitor-python/) | Python | Global IP Failover Monitor — monitor Global IP endpoints across regions, auto-failover between healthy endpoints. |
| [insurance-claims-intake-python](./insurance-claims-intake-python/) | Python | Policyholder calls, AI collects incident details, accepts photos via MMS, creates claim, assigns adjuster, texts status updates. Adjuster reviews AI-prepared claim. |
| [maintenance-request-dispatch-python](./maintenance-request-dispatch-python/) | Python | Tenant texts issue, AI categorizes and estimates cost, auto-dispatches vendor for routine work, manager approves orders over $500 via SMS reply. |
| [missions-ai-task-runner-python](./missions-ai-task-runner-python/) | Python | Missions AI Task Runner — AI-driven task execution within the Telnyx Missions framework. AI decides next steps based on task results. |
| [multi-channel-ai-helpdesk-with-ticketing-python](./multi-channel-ai-helpdesk-with-ticketing-python/) | Python | Multi-Channel AI Helpdesk with Ticketing — voice + SMS + WhatsApp support with auto-ticket creation. |
| [multi-party-ai-training-call-python](./multi-party-ai-training-call-python/) | Python | AI plays customer roles for sales/support practice. Multiple trainees join, AI rotates scenarios and scores each trainee. |
| [omnichannel-ai-receptionist-python](./omnichannel-ai-receptionist-python/) | Python | Voice and SMS application powered by Telnyx AI Inference. Built with Telnyx AI Assistants, AI Inference, Migration, Number Porting. |
| [policy-renewal-campaign-python](./policy-renewal-campaign-python/) | Python | Automated multi-channel renewal reminders. 60 days: SMS. 30 days: AI voice call reviewing coverage changes. 7 days: urgent SMS. Agent reviews lapsed policies for win-back. |
| [restaurant-reservation-waitlist-python](./restaurant-reservation-waitlist-python/) | Python | AI answers calls, checks table availability, books or adds to waitlist, texts when table is ready. Host reviews large party requests. |
| [run-llm-inference-nodejs](./run-llm-inference-nodejs/) | Node.js | run llm inference nodejs. |
| [run-llm-inference-python](./run-llm-inference-python/) | Python | Application powered by Telnyx AI Inference. Built with Telnyx AI Inference, Migration, Number Porting, SMS/MMS. |
| [storage-voicemail-archive-python](./storage-voicemail-archive-python/) | Python | Storage Voicemail Archive — record voicemails to Telnyx Cloud Storage with search. |
| [texml-voicemail-drop-python](./texml-voicemail-drop-python/) | Python | TeXML Voicemail Drop — leave pre-recorded voicemails at scale via TeXML. |
| [three-way-ai-interpreter-python](./three-way-ai-interpreter-python/) | Python | Two humans speak different languages on the same call. AI translates in real-time and speaks the translation to each party. |
| [video-room-ai-meeting-moderator-python](./video-room-ai-meeting-moderator-python/) | Python | Video Room AI Meeting Moderator — create video rooms with AI-powered agenda tracking and time management. |
| [video-room-ai-moderator-python](./video-room-ai-moderator-python/) | Python | Video Room AI Moderator — create video rooms with AI-powered content moderation on chat and participant management. |
| [voice-journal-daily-log-python](./voice-journal-daily-log-python/) | Python | Voice Journal Daily Log — call a number, speak your daily journal entry, AI transcribes and organizes it with mood, topics, and gratitude extraction. |
| [warm-transfer-ai-briefing-python](./warm-transfer-ai-briefing-python/) | Python | When an agent transfers a call, AI summarizes the conversation and briefs the next agent before connecting. No cold handoffs. |
| [webhook-debugger-ai-assistant-python](./webhook-debugger-ai-assistant-python/) | Python | Webhook Debugger AI Assistant — catch, inspect, and debug Telnyx webhooks with AI explanations. |
| [webrtc-ai-interpreter-live-calls-python](./webrtc-ai-interpreter-live-calls-python/) | Python | WebRTC AI Interpreter for Live Calls — real-time translation between two callers speaking different languages. |

## SIP Trunking

Connect your PBX or SBC to [Telnyx SIP Trunking](https://telnyx.com/products/sip-trunks) — trunk setup, inbound routing, failover, and codec configuration.

| Example | Language | Description |
|---------|----------|-------------|
| [setup-sip-trunk-python](./setup-sip-trunk-python/) | Python | Set up a SIP trunk connection with Telnyx. |
| [inbound-sip-routing-python](./inbound-sip-routing-python/) | Python | Route inbound SIP calls to your endpoints. |
| [sip-failover-routing-python](./sip-failover-routing-python/) | Python | Configure failover routing for SIP connections. |
| [configure-sip-codecs-python](./configure-sip-codecs-python/) | Python | Configure audio codecs for SIP trunks. |
| [setup-sip-trunk-nodejs](./setup-sip-trunk-nodejs/) | Node.js | Set up a SIP trunk connection with Telnyx. |
| [inbound-sip-routing-nodejs](./inbound-sip-routing-nodejs/) | Node.js | Route inbound SIP calls to your endpoints. |
| [setup-sip-trunk-go](./setup-sip-trunk-go/) | Go | Set up a SIP trunk connection with Telnyx. |
| [setup-sip-trunk-java](./setup-sip-trunk-java/) | Java | Set up a SIP trunk connection with Telnyx. |
| [setup-sip-trunk-csharp](./setup-sip-trunk-csharp/) | C# | Set up a SIP trunk connection with Telnyx. |
| [setup-sip-trunk-php](./setup-sip-trunk-php/) | PHP | Create, list, and retrieve a Telnyx credential (SIP) connection. |
| [setup-sip-trunk-ruby](./setup-sip-trunk-ruby/) | Ruby | Create, list, and retrieve a Telnyx credential (SIP) connection. |
| [sip-load-balancer-health-check-python](./sip-load-balancer-health-check-python/) | Python | SIP Load Balancer Health Check — monitor SIP trunk health across multiple endpoints, auto-failover to healthy trunks, track uptime metrics. |
| [sip-trunking-failover-monitor-python](./sip-trunking-failover-monitor-python/) | Python | SIP Trunking Failover Monitor — health-check SIP connections, auto-failover, SMS alerts. |

## IoT & SIM Management

Activate SIM cards, monitor data usage, provision eSIMs, and track device locations with the [Telnyx IoT platform](https://telnyx.com/products/iot-sim-card).

| Example | Language | Description |
|---------|----------|-------------|
| [activate-sim-card-python](./activate-sim-card-python/) | Python | Activate a SIM card on the Telnyx network. |
| [monitor-iot-data-usage-python](./monitor-iot-data-usage-python/) | Python | Monitor data usage for IoT SIM cards. |
| [provision-esim-python](./provision-esim-python/) | Python | Provision eSIM profiles over the air. |
| [track-iot-device-location-python](./track-iot-device-location-python/) | Python | Track the geographic location of IoT devices. |
| [activate-sim-card-nodejs](./activate-sim-card-nodejs/) | Node.js | Activate a SIM card on the Telnyx network. |
| [monitor-iot-data-usage-nodejs](./monitor-iot-data-usage-nodejs/) | Node.js | Monitor data usage for IoT SIM cards. |
| [activate-sim-card-go](./activate-sim-card-go/) | Go | Activate a SIM card on the Telnyx network. |
| [activate-sim-card-csharp](./activate-sim-card-csharp/) | C# | Enable (activate) a SIM card on the Telnyx network. |
| [activate-sim-card-php](./activate-sim-card-php/) | PHP | Activate a SIM card on the Telnyx network. |
| [activate-sim-card-java](./activate-sim-card-java/) | Java | Activate a SIM card on the Telnyx network. |
| [activate-sim-card-ruby](./activate-sim-card-ruby/) | Ruby | Enable (activate) a SIM card on the Telnyx network. |
| [iot-fleet-alert-escalation-python](./iot-fleet-alert-escalation-python/) | Python | IoT Fleet Alert Escalation — severity-based routing from IoT sensors to SMS, calls, and multi-party conferences. |
| [iot-panic-button-voice-alert-python](./iot-panic-button-voice-alert-python/) | Python | IoT Panic Button Voice Alert — IoT device triggers SIM-based alert, system calls emergency contacts with location and status. |
| [iot-smart-building-voice-control-python](./iot-smart-building-voice-control-python/) | Python | IoT Smart Building Voice Control — call a number to control building systems via AI + IoT SIMs. |
| [sim-fleet-data-usage-anomaly-detector-python](./sim-fleet-data-usage-anomaly-detector-python/) | Python | SIM Fleet Data Usage Anomaly Detector — monitor IoT SIM usage, AI detects anomalies, SMS alerts. |
| [voice-activated-iot-command-python](./voice-activated-iot-command-python/) | Python | Voice-Activated IoT Command — call a number, speak commands to control IoT devices. AI interprets natural language into device actions dispatched via SIM API. |
| [wireless-fleet-activation-portal-python](./wireless-fleet-activation-portal-python/) | Python | Wireless Fleet Activation Portal — bulk activate SIMs with status tracking. |

---

## What Is Telnyx?

Telnyx is an **AI Communications Infrastructure** platform that provides a single, integrated API for:

- **[Voice AI](https://telnyx.com/products/voice-ai-agents)** — Programmable voice with Call Control, IVR, recording, conferencing, and WebRTC.
- **[SMS & MMS](https://telnyx.com/products/sms-api)** — Send and receive messages globally with delivery receipts and webhook events.
- **[SIP Trunking](https://telnyx.com/products/sip-trunks)** — Connect your existing PBX with elastic SIP trunks, failover routing, and codec control.
- **[AI Assistants](https://telnyx.com/ai-assistants)** — Deploy LLM-powered voice and messaging agents with built-in telephony.
- **[IoT & SIM](https://telnyx.com/products/iot-sim-card)** — Global IoT connectivity with SIM management, eSIM provisioning, and data monitoring.

Unlike stitching together multiple vendors into a Frankenstack, Telnyx gives you one platform, one API key, and one bill. Calls and messages traverse the Telnyx-owned private IP network for lower latency and higher reliability.

## How to Get a Telnyx API Key

1. Sign up at [portal.telnyx.com](https://portal.telnyx.com).
2. Navigate to **API Keys** in the left sidebar.
3. Click **Create API Key** and copy the key.
4. Add it to your `.env` file as `TELNYX_API_KEY=your_key_here`.

Telnyx offers free trial credit for testing.

## FAQ

**Q: What programming languages are supported?**

These examples cover Python, Node.js, Go, and Ruby. Telnyx also provides official SDKs for Java, PHP, and C#.

**Q: Are these examples production-ready?**

Yes. Every example includes error handling, environment-based configuration, and Telnyx webhook signature verification. Review security and scaling considerations before deploying to production.

**Q: How is Telnyx different from Twilio?**

Telnyx is an AI Communications Infrastructure platform with a private global network. It offers integrated voice, messaging, AI, SIP, and IoT under one API — no need to stitch together multiple vendors. Telnyx also offers significantly lower pricing with no per-seat fees or contracts.

**Q: Do I need multiple vendors for voice, SMS, and AI?**

No. Telnyx provides voice, SMS/MMS, SIP trunking, AI assistants, and IoT SIM management through a single platform and API key.

**Q: Can I use these examples with my existing PBX?**

Yes. The SIP trunking examples show how to connect Telnyx to Asterisk, FreeSWITCH, 3CX, and other PBX systems.

**Q: Is there a free tier?**

Telnyx provides trial credit when you sign up. After that, pricing is pay-as-you-go with no minimums or contracts.

**Q: How do I get help?**

Check the Troubleshooting section in each example, visit [developers.telnyx.com](https://developers.telnyx.com), or reach out to [support@telnyx.com](mailto:support@telnyx.com).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on adding new examples.

## License

[MIT](./LICENSE)
