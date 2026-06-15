FairHire — Product Requirements Document
AI Interview Assistant for Bias-Free Hiring

Product Requirements Document | v1.0 | June 2025

Field	Value
Project Code	AI-01
Document Version	v1.0
Status	Draft — For Development
Team	FairHire Dev Team
Target	Hackathon MVP + Extensible Production Architecture
1. Executive Summary
FairHire is an AI-powered interview assistant that makes hiring more objective and equitable. It listens to or processes recorded interviews, transcribes them with speaker separation, runs real-time NLP analysis to detect bias and measure candidate engagement, suggests objective follow-up questions mid-interview, and generates a comprehensive post-interview report that evaluates candidates on merit-based criteria only.

The system combines on-device HuggingFace NLP models for classification, a RAG pipeline backed by Qdrant for grounded follow-up suggestion, Groq + Llama 3.3 70B as the single LLM for all generative tasks — powering both real-time follow-up suggestions and post-interview report generation via the same RAG pipeline. The frontend is built in React + Vite with Supabase as the relational backend.

FairHire addresses a measurable problem: unconscious bias in hiring interviews leads to inequitable outcomes and reduces organizational diversity. By automating the detection of problematic language patterns, standardizing evaluation criteria, and providing real-time interviewer guidance, FairHire creates a level playing field for all candidates.

2. Problem Statement
2.1 The Core Problem
Hiring interviews are inherently subjective. Interviewers — even well-intentioned ones — allow unconscious bias to influence their evaluations. Research consistently shows that candidates are judged differently based on name, gender, accent, age, appearance, and perceived socioeconomic background, independent of their actual competency.

Key documented problems include:

Differential question complexity: some candidates are asked harder technical questions than others for the same role
Gendered and loaded language used by interviewers that signals a non-neutral environment
Inconsistent evaluation criteria applied across candidates for the same position
Recency and halo effects distorting post-interview scoring
Interviewers forgetting to probe important competency areas, leading to incomplete evaluations
2.2 Why Existing Solutions Fall Short
Current approaches to bias mitigation in hiring are either manual (bias training workshops, structured interview guides) or post-hoc (auditing after hiring decisions are made). Neither approach provides real-time, automated assistance during the actual interview. FairHire fills this gap.

3. Goals and Non-Goals
3.1 Goals
Automatically transcribe interview audio with speaker diarization (interviewer vs candidate separation)
Detect bias patterns in interviewer language in real-time with explanations
Analyze candidate sentiment and engagement across the interview arc
Suggest objective, role-relevant follow-up questions mid-interview using a RAG pipeline
Generate a comprehensive post-interview evaluation report using the RAG pipeline + Groq + Llama 3.3 70B
Store all interviews, transcripts, and reports in Supabase for longitudinal analysis
Provide a clean, professional React UI for both live and recorded interview modes
3.2 Non-Goals (v1.0)
FairHire does not make hiring decisions — it provides information to human decision-makers
FairHire does not record video — audio only in v1.0
FairHire does not integrate with ATS systems (Workday, Greenhouse) in v1.0
FairHire does not support multi-language interviews beyond English in v1.0
FairHire does not provide real-time audio streaming — it processes audio chunks or uploaded files
4. User Personas
Persona	Role	Primary Need	Key Pain Point
The Interviewer	Hiring manager or recruiter conducting the interview	Real-time follow-up question suggestions and bias alerts	Forgets to probe key competencies; unconsciously favors similar candidates
The HR Admin	HR team member managing the hiring process	Centralized reports and audit trail across all interviews	No standardized way to compare candidates across interviewers
The Candidate	Job applicant being interviewed	A fair, consistent, merit-based evaluation	Evaluated on subjective impressions rather than demonstrated skills
The Compliance Officer	Legal or DEI officer in the organization	Evidence of bias-free process for regulatory or audit purposes	Cannot currently prove hiring process is equitable
5. System Architecture
5.1 Architecture Overview
FairHire is an 8-layer system. Each layer has a distinct responsibility and communicates with adjacent layers via well-defined interfaces. The two primary data flows are:

Real-time flow: Audio input → Whisper transcription → NLP analysis → RAG pipeline → Groq LLM → follow-up suggestion panel on frontend
Post-interview flow: Complete transcript + NLP scores → RAG pipeline (Qdrant) → Groq + Llama 3.3 70B → comprehensive evaluation report → frontend report view
5.2 Layer-by-Layer Breakdown
Layer 1 — Frontend (React + Vite + Tailwind CSS)
The frontend is a single-page React application built with Vite for fast development and hot module replacement. It communicates with the FastAPI backend via REST API calls using axios or the native fetch API.

Key views and components:

Interviewer Dashboard: Audio file upload interface or live microphone capture button. Displays job role selector, candidate name input, and interview start controls.
Real-time Suggestion Panel: A floating sidebar that updates after every 2-3 exchanges with 3 suggested follow-up questions retrieved from the RAG pipeline.
Live Transcript View: Shows the rolling diarized transcript as the interview progresses, with interviewer and candidate turns color-coded.
Post-Interview Report View: Renders the final structured report including bias score, sentiment arc chart, engagement metrics, and merit-based candidate evaluation.
Admin Dashboard: Lists all past interview sessions with sortable scores and downloadable reports.
Tech stack: React 18, Vite 5, Tailwind CSS, Recharts (for sentiment arc visualization), Supabase JS client.

Layer 2 — Backend API (FastAPI + Python)
The FastAPI backend is the central orchestration layer. It receives requests from the frontend, coordinates the transcription, NLP, and RAG pipeline, and returns structured JSON responses.

API routes:

POST /upload — Receives audio file as multipart form data. Calls Whisper API for transcription. Returns diarized transcript JSON.
POST /analyze — Receives full or partial transcript. Runs sentiment analysis, bias detection, and engagement scoring in sequence. Returns structured analysis JSON.
POST /suggest — Receives last 2-3 transcript exchanges + job role. Runs RAG pipeline to retrieve context. Calls Groq API for follow-up generation. Returns 3 follow-up question strings.
POST /report — Receives full transcript + all analysis results. Embeds transcript, queries Qdrant for relevant context, calls Groq + Llama 3.3 70B for report generation. Returns report markdown.
GET/POST /sessions — CRUD operations on interview sessions stored in Supabase.
Tech stack: FastAPI, Uvicorn, Pydantic for request/response validation, httpx for async external API calls, transformers and torch for HuggingFace models.

Layer 3 — Transcription (OpenAI Whisper API)
Audio input from the frontend is sent to the FastAPI /upload endpoint, which forwards it to the OpenAI Whisper API. Whisper returns a transcript with speaker diarization — it separates and labels the interviewer and candidate speech turns.

Output format:

Speaker 1 (Interviewer): [spoken text]
Speaker 2 (Candidate): [spoken text]
The diarized transcript is then stored in Supabase and passed downstream to the NLP pipeline. For the hackathon demo, the Whisper API endpoint is used (no local model hosting required). Supported audio formats: MP3, WAV, M4A, WEBM.

Layer 4 — NLP Analysis Pipeline (HuggingFace Models)
All NLP models are loaded once at FastAPI startup and called per-request. They run inside the Python server process — no external API calls, no per-call cost.

4A — Sentiment Analysis

Model: cardiffnlp/twitter-roberta-base-sentiment-latest
Input: Candidate speech turns only (filtered from diarized transcript)
Output: Positive / Negative / Neutral score per candidate response
Aggregation: Scores are aggregated across the timeline to produce an emotional arc (early confidence, mid-interview stress, closing energy)
Use in report: Flagged if candidate sentiment degrades sharply, suggesting interviewer tone may have caused stress
4B — Bias Detection

Model: d4data/bias-detection-model
Input: Interviewer speech turns only
Output: Bias flag (boolean) + confidence score + flagged phrase
Flag types: Gendered language, loaded phrasing, legally problematic questions (family status, age, religion), differential complexity signals
Real-time: Runs after every interviewer turn during live sessions
4C — Engagement Scoring

No ML model — pure Python statistics computed on the transcript
Metrics computed: Average candidate response length (word count), interviewer-to-candidate talk time ratio, number of follow-up exchange pairs, vocabulary diversity score (type-token ratio), number of clarifying questions asked by candidate
Output: Normalized engagement score 0–10
Low engagement score flags: Candidate giving very short answers, extreme talk time imbalance, no clarification requests
Layer 5 — RAG Pipeline (Qdrant + Sentence Transformers + Groq)
The RAG pipeline powers the real-time follow-up suggestion feature. It grounds the LLM in curated institutional knowledge about good interviewing practice, preventing the generic repetitive output that comes from using an LLM with no context.

Step-by-step flow:

Embedding: The last 2-3 exchanges from the current transcript are embedded using sentence-transformers/all-MiniLM-L6-v2. This produces a 384-dimensional dense vector representing the current conversational context.
Vector Search: The embedding is used to query Qdrant Cloud (free tier) for the top 5 most semantically similar chunks from the knowledge base. Search is filtered by metadata — role type and competency area.
Context Retrieval: Retrieved chunks are assembled into a context string. These may include similar past interview segments, relevant follow-up question templates, or HR guideline excerpts.
LLM Generation: The current transcript excerpt + retrieved context + job description chunks are passed to Groq (Llama 3.3 70B) with a carefully structured system prompt. Groq is used here for its low latency — suggestions need to appear within 2-3 seconds of the last exchange.
Output: 3 specific, role-relevant, competency-mapped follow-up questions are returned and displayed in the suggestion panel.
Knowledge Base Contents (Qdrant)

Data Type	Volume	Source	Metadata Tags
Synthetic interview transcripts	30 documents	Generated via Claude/GPT-4	role, seniority, outcome (good/biased)
Bias flag examples with rewrites	50-100 pairs	WinoBias dataset, EEOC guidelines	bias_type, severity
Role-specific follow-up questions	100-200 questions	SHRM guides, Google reWork	role, competency, question_type
Job descriptions	20-30 documents	Kaggle job descriptions dataset	role, seniority, industry
HR best practice guidelines	10-15 chunked docs	EEOC, SHRM, LinkedIn, Google reWork	topic, authority_level
Layer 6 — Final Report Generation (RAG Pipeline + Groq + Llama 3.3 70B)
After the interview ends, the same RAG pipeline used for real-time suggestions is invoked again — but now with the full transcript as the query context and a report-generation system prompt. The complete transcript, all NLP analysis results, and bias flags are embedded, the top relevant chunks from Qdrant are retrieved (bias examples, HR guidelines, good evaluation frameworks), and Groq + Llama 3.3 70B generates the full structured report. The same Qdrant knowledge base and embedding model (all-MiniLM-L6-v2) are reused — no additional infrastructure required.

Report sections generated:

Executive summary: 3-4 sentence overview of interview quality and key findings
Bias analysis: Plain English explanation of each bias flag raised, with the specific phrase that triggered it and suggested alternative phrasing
Candidate evaluation: Merit-based assessment of candidate performance across competencies defined in the job description, with no reference to demographic signals
Interviewer feedback: Specific, actionable suggestions for the interviewer to improve fairness in future interviews
Overall fairness score: A normalized 0-100 score for the interview's fairness, with breakdown by bias category
Layer 7 — Relational Database (Supabase)
Supabase (PostgreSQL) stores all persistent data. The schema is designed to support both individual interview sessions and longitudinal analytics across multiple interviews for the same role or interviewer.

Table	Key Fields	Purpose
interviews	id, interviewer_id, candidate_name, role, created_at, status	Session metadata
transcripts	id, interview_id, speaker, text, timestamp, turn_index	Full diarized transcript storage
analysis_results	id, interview_id, sentiment_scores, bias_flags, engagement_score	NLP analysis output
reports	id, interview_id, report_markdown, fairness_score, generated_at	Generated reports
job_descriptions	id, role, seniority, description_text, company_id	JD storage for RAG context
users	id, email, role (interviewer/admin), created_at	Auth and access control
Layer 8 — Deployment
Component	Service	Tier	Notes
Frontend (React)	Vercel	Free	Auto-deploy from GitHub main branch
Backend (FastAPI)	Render	Free	HuggingFace models loaded on startup; ~500MB RAM usage
Vector DB	Qdrant Cloud	Free tier	1GB storage, sufficient for hackathon knowledge base
Relational DB	Supabase	Free tier	500MB DB, 2GB bandwidth
Transcription	OpenAI Whisper API	Pay-per-use	$0.006/minute of audio
Real-time LLM	Groq API	Free tier	14,400 requests/day on free plan
Report LLM	Groq + Llama 3.3 70B	Free tier	Same as suggestions — via RAG pipeline
Audio for demo	ngrok (local)	Free	Expose local FastAPI for hackathon demo if needed
6. Feature Specifications
Feature 1 — Audio Upload and Transcription
The interviewer uploads a recorded interview audio file (MP3, WAV, M4A) via the frontend upload interface. The file is sent to /upload, forwarded to Whisper, and the diarized transcript is returned and displayed in the Live Transcript View. For the hackathon demo, recorded files are preferred over live streaming to reduce complexity.

Acceptance criteria:

Accepts audio files up to 25MB
Returns diarized transcript within 30 seconds for a 30-minute interview
Correctly identifies and labels at least 2 speakers
Displays transcript in real-time scrolling view with interviewer/candidate turns visually distinct
Feature 2 — Real-time Bias Detection
After each interviewer speech turn is transcribed, the bias detection model runs on that turn and displays any flags immediately in the interviewer UI. Flags include the specific phrase, the bias category, and a suggested alternative phrasing.

Acceptance criteria:

Bias flag appears within 3 seconds of the interviewer turn being transcribed
Flag includes: flagged phrase (highlighted in transcript), bias type label, confidence score, suggested alternative
False positive rate acceptable for demo: <20% on test set of 20 manually labeled interview turns
Feature 3 — Follow-up Question Suggestions (RAG Pipeline)
After every 2-3 exchanges, the RAG pipeline generates 3 role-relevant follow-up questions and displays them in the suggestion panel. The interviewer can click any suggestion to copy it to their clipboard.

Acceptance criteria:

Suggestions appear within 3 seconds of triggering
Suggestions are role-specific (different questions for engineer vs PM roles)
Suggestions are non-repetitive across the interview session
Suggestions map to specific competencies from the job description
Feature 4 — Post-Interview Report
After the interviewer clicks 'End Interview', the system runs the full RAG pipeline one final time with the complete transcript as input. Qdrant retrieves the most relevant bias examples, HR evaluation guidelines, and competency frameworks. Groq + Llama 3.3 70B generates the structured report using this grounded context. The report is rendered in the Report View and stored in Supabase.

Acceptance criteria:

Report generated within 20 seconds of interview end
Report includes all 5 sections: executive summary, bias analysis, candidate evaluation, interviewer feedback, fairness score
Bias analysis references specific transcript quotes
Candidate evaluation references specific job description competencies
Report is downloadable as PDF
Feature 5 — Admin Dashboard
HR admins can view all past interview sessions, filter by role, date, and fairness score, and download any report. Longitudinal trends (average fairness score per interviewer, bias flag frequency over time) are displayed as summary charts.

Acceptance criteria:

Lists all interview sessions with name, role, date, fairness score
Filterable and sortable by all columns
Each row links to the full report
Summary stats bar shows: total interviews, average fairness score, most common bias type
7. Data Flow Specifications
7.1 Real-time Flow
Interviewer uploads audio file or starts recording via frontend
Frontend sends audio to POST /upload
FastAPI forwards audio to OpenAI Whisper API
Whisper returns diarized transcript JSON with speaker labels and timestamps
FastAPI stores transcript in Supabase transcripts table
FastAPI splits transcript by speaker: interviewer turns → bias model, candidate turns → sentiment model
Bias flags and sentiment scores stored in Supabase analysis_results table
Every 2-3 exchanges: FastAPI embeds last exchanges, queries Qdrant, retrieves context, calls Groq
Groq returns 3 follow-up suggestions; FastAPI returns them to frontend suggestion panel
Frontend displays suggestions; interviewer selects or ignores
7.2 Post-interview Flow
Interviewer clicks 'End Interview' on frontend
Frontend sends POST /report with session ID
FastAPI retrieves full transcript, all bias flags, sentiment scores, and engagement score from Supabase
FastAPI embeds full transcript, queries Qdrant for top 8 relevant chunks (bias examples, HR guidelines, evaluation frameworks)
Groq + Llama 3.3 70B returns full report markdown
FastAPI stores report in Supabase reports table, returns markdown to frontend
Frontend renders report in Report View with PDF download option
8. Complete Tech Stack Reference
Category	Technology	Version / Model	Purpose
Frontend framework	React	18.x	UI components and state management
Build tool	Vite	5.x	Dev server and production bundling
CSS	Tailwind CSS	3.x	Utility-first styling
Charts	Recharts	2.x	Sentiment arc visualization
Backend framework	FastAPI	0.111+	REST API and pipeline orchestration
Python runtime	Python	3.11+	Backend language
Transcription	OpenAI Whisper API	whisper-1	Audio-to-text with diarization
Sentiment model	HuggingFace Transformers	cardiffnlp/twitter-roberta-base-sentiment-latest	Candidate sentiment classification
Bias model	HuggingFace Transformers	d4data/bias-detection-model	Interviewer bias detection
Embedding model	Sentence Transformers	all-MiniLM-L6-v2	RAG query embedding (384-dim)
Vector database	Qdrant	Cloud free tier	Semantic search for RAG pipeline
Real-time LLM	Groq + Llama	Llama 3.3 70B	Low-latency follow-up generation
Report LLM	Groq + Llama 3.3 70B	llama-3.3-70b-versatile	Post-interview report via RAG + Groq
Relational DB	Supabase	PostgreSQL 15	Sessions, transcripts, reports
Auth	Supabase Auth	—	User authentication and RLS
Frontend deploy	Vercel	—	Static hosting with CI/CD
Backend deploy	Render	—	Python server hosting
Local tunnel	ngrok	—	Demo API exposure if needed
9. RAG Knowledge Base Specification
9.1 Data Sources
The Qdrant knowledge base is pre-populated before the application is deployed. All sources are publicly available or synthetically generated.

Synthetic Interview Transcripts

Volume: 30 transcripts across 4 roles (software engineer, product manager, data analyst, marketing manager)
Generation: Prompted via any LLM (Claude, GPT-4, or Groq) offline before deployment — this is a one-time data preparation step, not a runtime dependency
Ground truth labels: Each transcript is labeled with known bias instances and quality scores for evaluation
Bias Flag Examples

Source: WinoBias dataset (HuggingFace), EEOC interview guidelines, MIT audit studies
Format: Biased phrase → unbiased rewrite pairs
Volume: 50-100 pairs covering gender bias, age bias, family status bias, accent/origin bias
Follow-up Question Banks

Sources: SHRM competency-based interview guides, Google reWork hiring documentation, Exponent PM question bank
Organization: Questions tagged by role, competency (problem-solving, collaboration, technical depth, communication), and question type (behavioral, situational, technical)
Volume: 100-200 questions across 4 roles
Job Descriptions

Source: Kaggle job descriptions dataset (jacob-hugging-face/job-descriptions), manually curated additions
Volume: 20-30 JDs across target roles
Used for: Grounding follow-up suggestions in actual role requirements
HR Best Practice Guidelines

Sources: EEOC Uniform Guidelines, SHRM Interview Guide, Google reWork Structured Hiring Guide, LinkedIn Structured Hiring Documentation
Chunking strategy: 256-512 token chunks with 50-token overlap
Volume: 10-15 documents producing approximately 200-400 chunks
9.2 Ingestion Pipeline
The knowledge base is built by running a one-time Python ingestion script before deployment:

Load all source documents from local files
Split into 256-512 token chunks using LangChain RecursiveCharacterTextSplitter
Embed each chunk using sentence-transformers/all-MiniLM-L6-v2
Upsert into Qdrant with payload metadata: type, role, competency, source, chunk_index
Total expected chunks: 500-800, well within Qdrant free tier limits
10. API Contracts
POST /upload
Field	Type	Description
Request body	multipart/form-data	audio_file: binary, interview_id: string, role: string
Response 200	JSON	{ transcript: [{speaker: string, text: string, start: float, end: float}], interview_id: string }
Response 400	JSON	{ error: 'Unsupported file format' }
Response 500	JSON	{ error: 'Whisper API error', detail: string }
POST /analyze
Field	Type	Description
Request body	JSON	{ interview_id: string, transcript: array, role: string }
Response 200	JSON	{ sentiment_scores: array, bias_flags: array, engagement_score: float, summary_stats: object }
bias_flags item	JSON	{ phrase: string, bias_type: string, confidence: float, suggestion: string, turn_index: int }
sentiment_scores item	JSON	{ turn_index: int, label: string, score: float }
POST /suggest
Field	Type	Description
Request body	JSON	{ interview_id: string, recent_exchanges: array, role: string, competencies_covered: array }
Response 200	JSON	{ suggestions: [string, string, string], competency_tags: array }
recent_exchanges	array	Last 2-3 transcript turns as [{speaker, text}]
POST /report
Field	Type	Description
Request body	JSON	{ interview_id: string }
Response 200	JSON	{ report_markdown: string, fairness_score: float, report_id: string }
Response 404	JSON	{ error: 'Interview session not found' }
11. Supabase Schema
All tables use UUID primary keys and include created_at timestamps. Row Level Security (RLS) is enabled on all tables — interviewers can only access their own sessions; admins have full read access.

Table	Column	Type	Constraints
interviews	id	UUID	PK, default gen_random_uuid()
interviews	interviewer_id	UUID	FK → users.id
interviews	candidate_name	TEXT	NOT NULL
interviews	role	TEXT	NOT NULL
interviews	status	TEXT	CHECK IN (pending, active, completed)
interviews	created_at	TIMESTAMPTZ	DEFAULT now()
transcripts	id	UUID	PK
transcripts	interview_id	UUID	FK → interviews.id
transcripts	speaker	TEXT	CHECK IN (interviewer, candidate)
transcripts	text	TEXT	NOT NULL
transcripts	turn_index	INTEGER	NOT NULL
transcripts	timestamp_start	FLOAT	Seconds from audio start
analysis_results	id	UUID	PK
analysis_results	interview_id	UUID	FK → interviews.id, UNIQUE
analysis_results	sentiment_scores	JSONB	Array of per-turn scores
analysis_results	bias_flags	JSONB	Array of flag objects
analysis_results	engagement_score	FLOAT	0.0 to 10.0
reports	id	UUID	PK
reports	interview_id	UUID	FK → interviews.id, UNIQUE
reports	report_markdown	TEXT	Generated report
reports	fairness_score	FLOAT	0.0 to 100.0
reports	generated_at	TIMESTAMPTZ	DEFAULT now()
12. Groq Report Generation Prompt Template
The following is the system + user prompt structure sent to Groq + Llama 3.3 70B for report generation. The RAG-retrieved context chunks are injected into the system prompt before the transcript. This should be hardcoded in the FastAPI /report handler.

System Prompt:

You are an expert HR analyst specializing in bias-free hiring. You receive interview transcripts,
NLP analysis results, and bias flags. Your job is to generate a comprehensive, objective,
evidence-based post-interview evaluation report. Always reference specific transcript quotes when
citing bias or candidate strengths. Never make inferences about demographic characteristics.
Focus exclusively on demonstrated competencies.
User Prompt:

Role: {role} | Candidate: {candidate_name} | Duration: {duration} minutes

TRANSCRIPT: {full_transcript}

BIAS FLAGS: {bias_flags_json}

SENTIMENT SCORES: {sentiment_scores_json}

ENGAGEMENT SCORE: {engagement_score}/10

Generate the full report with sections: Executive Summary, Bias Analysis, Candidate Evaluation,
Interviewer Feedback, Fairness Score.
13. Hackathon Demo Plan
13.1 What to Show Judges
Upload a pre-recorded mock interview audio file (2-3 minutes, prepared in advance)
Show the transcript appearing with speaker labels in real-time
Show a bias flag appearing on a prepared example of biased interviewer language
Show the suggestion panel updating with 3 role-specific follow-up questions
Click 'Generate Report' and show the full generated evaluation appearing
Show the admin dashboard with a few pre-seeded past interviews and fairness score trends
13.2 Demo Data Preparation
Prepare 1 high-quality 3-minute mock interview audio file with 2 deliberate bias flags and 1 example of excellent candidate response
Pre-seed Supabase with 5-6 past interview sessions showing varied fairness scores for the admin dashboard
Pre-populate Qdrant with the full knowledge base (ingestion script run before demo)
Test all three API routes with the demo audio at least 3 times before presentation
13.3 Fallback Plan
If API calls fail during demo (network issues, quota exhaustion):

Keep a static pre-generated report JSON locally and load it as a mock /report response
Keep pre-computed bias flags and suggestions as fallback fixtures in the frontend
Keep ngrok running as backup if Render deployment has cold start issues
14. Development Milestones
Milestone	Deliverables	Priority
M1 — Backend skeleton	FastAPI project with 4 routes returning mock data, Supabase schema migrated, env vars configured	P0
M2 — Transcription pipeline	Whisper API integration working, diarized transcript returned from /upload	P0
M3 — NLP models	Sentiment + bias models loaded and returning results from /analyze	P0
M4 — Qdrant knowledge base	Ingestion script run, all 5 data categories loaded, /suggest returning real results	P0
M5 — RAG report	/report endpoint running RAG pipeline + Groq and returning formatted markdown	P0
M6 — Frontend core	Upload UI, transcript view, suggestion panel, report view all connected to real backend	P0
M7 — Demo polish	Demo audio prepared, Supabase seeded, all fallbacks in place, admin dashboard working	P1
M8 — Stretch features	PDF export, real-time mic recording, multi-role comparison view	P2
15. Risks and Mitigations
Risk	Likelihood	Impact	Mitigation
Whisper API quota exhaustion during demo	Medium	High	Pre-transcribe demo audio; cache result in Supabase
Groq rate limit hit during demo	Low	Medium	Pre-cache suggestion responses for demo transcript
HuggingFace models too slow on free Render tier	High	Medium	Run backend locally with ngrok for demo; optimize batch size
Qdrant cold start latency on free tier	Medium	Low	Pre-warm Qdrant with a dummy query before demo starts
Bias model producing too many false positives	Medium	Medium	Tune confidence threshold; use carefully curated demo audio
Groq report quality vs suggestions	Low	Medium	Use a more detailed system prompt and larger context window for /report vs /suggest
16. Glossary
Term	Definition
Diarization	The process of separating an audio transcript by speaker identity (Speaker 1 vs Speaker 2)
RAG	Retrieval-Augmented Generation — a technique where an LLM is given relevant retrieved documents as context before generating a response
Qdrant	An open-source vector database optimized for semantic similarity search
Embedding	A dense numerical vector representation of text that captures semantic meaning
Bias flag	An automated alert raised when the bias detection model identifies potentially biased language in an interviewer turn
Fairness score	A normalized 0-100 score representing how free from detected bias an interview was, computed by Groq + Llama 3.3 70B during the RAG report generation step
Engagement score	A 0-10 score computed from transcript statistics measuring candidate participation and responsiveness
EEOC	Equal Employment Opportunity Commission — the US federal agency responsible for enforcing anti-discrimination hiring laws
SHRM	Society for Human Resource Management — the leading professional HR organization that publishes hiring best practice guides
Turn	One continuous speech segment from a single speaker before the other speaker begins
End of Document — FairHire PRD v1.0 | June 2025
