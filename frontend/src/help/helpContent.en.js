/**
 * AnomalyMatrix Help — end users only (Operator, QA, Engineer)
 * Focus: HMI operation and features, no installation/IT
 */

export const HELP_CATEGORIES = [
  { id: 'application', label: 'Application & Use Cases', icon: '🏭' },
  { id: 'start', label: 'Getting Started', icon: '🚀' },
  { id: 'screens', label: 'Screens', icon: '🖥️' },
  { id: 'workflow', label: 'Workflows', icon: '🔄' },
  { id: 'roles', label: 'Roles', icon: '👤' },
  { id: 'decisions', label: 'Decisions & KPIs', icon: '📊' },
  { id: 'faq', label: 'FAQ', icon: '❓' },
  { id: 'glossary', label: 'Glossary', icon: '📖' },
];

export const HELP_ARTICLES = [
  {
    id: 'what-is-anomalymatrix',
    category: 'application',
    title: 'What is AnomalyMatrix for?',
    keywords: ['application', 'purpose', 'use', 'software', 'quality', 'vision'],
    summary: 'Automated anomaly detection on the production line — with operator HMI, PLC integration, and QA feedback.',
    featured: true,
    sections: [
      {
        heading: 'Core purpose',
        paragraphs: [
          'AnomalyMatrix inspects parts and surfaces on the line for deviations from the defined good part — without programming every possible defect in advance.',
          'The software learns from “good” references and reports unusual patterns as an anomaly score with a traffic-light decision (green / amber / red).',
          'Goal: detect defects early, reduce scrap, and keep the process stable.',
        ],
      },
      {
        heading: 'Typical use cases',
        paragraphs: [
          'Inline quality control after machining, bonding, welding, coating, or assembly.',
          '100% inspection at bottlenecks where manual visual checks are too slow or inconsistent.',
          'Retrofit on existing cells via OPC UA — triggers and stop signals to the PLC.',
          'Trend monitoring: detect process drift before serial defects occur.',
          'QS documentation and feedback: assessments feed audit trails and model improvement.',
        ],
      },
      {
        heading: 'What the software does',
        paragraphs: [
          'Trigger inspections (manually on the dashboard, automatically via PLC trigger, or OPC UA method).',
          'Capture images, score with the AI model, store results, and report to the machine.',
          'On red: stop and reject signals to the PLC (StopLineRequest, RejectPart).',
          'Operator HMI: latest inspections, detail with score and heatmap.',
          'QA feedback: confirm anomaly, mark false positive, or request review.',
          'Trends and KPIs: anomaly rate, cycle times, OPC UA error rate.',
        ],
      },
      {
        heading: 'Who uses it?',
        paragraphs: [
          'Operator: run inspections, read traffic lights, react to issues.',
          'QA lead: assess results, submit feedback for continuous improvement.',
          'Process engineer: monitor trends and recipe/model versions.',
          'Maintenance / automation: integrate the OPC UA interface into PLC logic.',
        ],
      },
      {
        heading: 'What it does not replace',
        paragraphs: [
          'Not a substitute for your plant’s formal release and hold processes — those remain with QS.',
          'Not fully automatic root-cause analysis — it provides clues (score, heatmap, defect class) for experts.',
          'Dimensional gauging only where defined in recipe and model.',
        ],
      },
    ],
    related: ['use-case-inline-qc', 'use-case-plc-automation', 'plc-opcua-signals', 'operator-daily-flow'],
  },
  {
    id: 'use-case-inline-qc',
    category: 'application',
    title: 'Inline quality control on the line',
    keywords: ['inline', 'line', '100 percent', 'inspection', 'scrap'],
    summary: 'Inspect every part without breaking takt time.',
    sections: [
      {
        heading: 'Scenario',
        paragraphs: [
          'After a process step (e.g. seam, coating, label), every part must be checked.',
          'The PLC releases the part or stops the line on red.',
        ],
      },
      {
        heading: 'Benefits',
        paragraphs: [
          'Consistent evaluation instead of sample-based manual checks.',
          'Immediate reaction: stop signal on clear anomalies.',
          'Traceable history per inspection (ID, time, score, decision).',
        ],
      },
      {
        heading: 'Typical flow',
        paragraphs: [
          'Part in position → PLC sets ExternalTrigger → inspection runs → result to PLC.',
          'Green: continue transport. Red: stop, hold part, notify QA.',
        ],
      },
    ],
    related: ['what-is-anomalymatrix', 'decision-colors', 'plc-opcua-signals'],
  },
  {
    id: 'use-case-process-monitoring',
    category: 'application',
    title: 'Process monitoring & drift',
    keywords: ['drift', 'trend', 'process', 'early warning', 'maintenance'],
    summary: 'Detect slow degradation before the batch fails.',
    sections: [
      {
        heading: 'Scenario',
        paragraphs: [
          'Wear, media changes, or parameter drift gradually raise anomaly scores.',
          'Single amber or red parts may be acceptable — the trend is the warning.',
        ],
      },
      {
        heading: 'Benefits',
        paragraphs: [
          'Trends page and dashboard KPIs show averages and anomaly rate.',
          'Early warning for maintenance or process correction before mass scrap.',
          'Comparison across shifts and recipe versions.',
        ],
      },
    ],
    related: ['trends-overview', 'engineer-trends-flow', 'what-is-anomalymatrix'],
  },
  {
    id: 'use-case-plc-automation',
    category: 'application',
    title: 'Automation with the PLC',
    keywords: ['automation', 'plc', 'opc', 'trigger', 'stop'],
    summary: 'Inspection and reaction without manual HMI steps.',
    sections: [
      {
        heading: 'Scenario',
        paragraphs: [
          'The PLC controls takt, camera trigger, and transport — AnomalyMatrix is the scoring engine.',
        ],
      },
      {
        heading: 'Benefits',
        paragraphs: [
          'No separate operator action for every inspection.',
          'Unified signals: Busy, ResultReady, DecisionCode, StopLineRequest.',
          'AcknowledgeStop for safe restart logic.',
        ],
      },
    ],
    related: ['plc-opcua-signals', 'what-is-anomalymatrix'],
  },
  {
    id: 'use-case-quality-loop',
    category: 'application',
    title: 'Quality assurance & continuous improvement',
    keywords: ['qa', 'feedback', 'learning', 'audit', 'documentation'],
    summary: 'Feed human expertise back into the system.',
    sections: [
      {
        heading: 'Scenario',
        paragraphs: [
          'The model reports anomalies — QA decides whether they are real defects or false alarms.',
        ],
      },
      {
        heading: 'Benefits',
        paragraphs: [
          'Feedback (confirm / false positive / review) documents the QS decision.',
          'Confirming an anomaly marks the inspection NOK (red) and stores the frame as a NOK sample.',
          'Audit log and events for traceability.',
        ],
      },
    ],
    related: ['qa-review-flow', 'what-is-anomalymatrix', 'glossary-feedback-verdict'],
  },
  {
    id: 'help-using-help',
    category: 'start',
    title: 'Using Help',
    keywords: ['help', 'search', 'f1', 'faq', 'guide'],
    summary: 'How to find answers directly in the interface.',
    sections: [
      {
        heading: 'Navigation',
        paragraphs: [
          'The "Help & FAQ" tab opens the full knowledge base.',
          'The help button (?) in the lower-right corner opens quick search.',
          'Press F1 to open the same quick help; Esc closes it.',
        ],
      },
      {
        heading: 'Context help',
        paragraphs: [
          'On Dashboard, Inspection Detail, Trends, and Configuration: link "Help for this area".',
          'This jumps directly to the topic that matches the current screen.',
        ],
      },
      {
        heading: 'Search',
        paragraphs: [
          'Enter keywords, e.g. "feedback", "red", "trend", "license", "pipeline".',
          'Categories on the left narrow the list.',
        ],
      },
    ],
    related: ['hmi-overview', 'operator-daily-flow'],
  },
  {
    id: 'hmi-overview',
    category: 'start',
    title: 'Interface overview',
    keywords: ['interface', 'navigation', 'tabs', 'start', 'overview'],
    summary: 'The main areas of the AnomalyMatrix interface.',
    sections: [
      {
        heading: 'Main navigation',
        paragraphs: [
          'Home — start inspections and see the last result.',
          'Quality — score, heatmap, and QA feedback.',
          'Training — capture good parts and activate models.',
          'Settings — recipes, thresholds, cameras, trends, license.',
          'Help via the question mark or Settings → Help.',
        ],
      },
      {
        heading: 'Connection status',
        paragraphs: [
          'Below the title you can see whether the inspection software is connected.',
          '"Backend connected" — live data from the line.',
          '"Offline seed data" — demo/fallback data; new inspections may not be available. Notify your supervisor or shift lead.',
        ],
      },
    ],
    related: ['operator-daily-flow', 'dashboard-overview'],
  },
  {
    id: 'operator-daily-flow',
    category: 'workflow',
    title: 'Typical operator workflow',
    keywords: ['operator', 'shift', 'workflow', 'inspection', 'daily'],
    summary: 'From starting an inspection to notifying QA.',
    sections: [
      {
        heading: 'Step by step',
        paragraphs: [
          '1. Open Home and check status (green = OK / ready).',
          '2. Start "Inspect" and wait for the result.',
          '3. Read the decision, score, and heatmap on Home.',
          '4. For review or NOK: open Quality and confirm QA.',
          '5. For red or unclear results: involve QA / shift lead; hold the part per plant rules.',
        ],
      },
      {
        heading: 'When green',
        paragraphs: [
          'The part may proceed unless additional plant rules apply.',
          'Keep an eye on Trends regularly — a single green result does not guarantee a stable process.',
        ],
      },
    ],
    related: ['dashboard-overview', 'decision-colors', 'pipeline-messages'],
  },
  {
    id: 'qa-review-flow',
    category: 'workflow',
    title: 'QA: Review inspection & feedback',
    keywords: ['qa', 'quality', 'feedback', 'review', 'false positive'],
    summary: 'How to document your assessment of an inspection.',
    sections: [
      {
        heading: 'When to give feedback?',
        paragraphs: [
          'After visual or measured re-check of the part.',
          'Especially important for NOK (red) and review (amber).',
          'Also for OK if you suspect a hidden defect.',
        ],
      },
      {
        heading: 'Submit feedback',
        paragraphs: [
          'Open Inspection Detail → section "QA Feedback".',
          'Select verdict: Confirm anomaly, False positive, or Re-check required.',
          'Optional comment (e.g. defect location, batch, shift).',
          '"Submit feedback" — on success you will see "Feedback saved."',
        ],
      },
      {
        heading: 'Effect',
        paragraphs: [
          'Confirming an anomaly shows the inspection as NOK (red), with an audit of the automatic decision.',
          'The inspection image is stored as a NOK sample for the recipe/camera (count on Configuration → Training).',
          'False positive keeps the automatic decision — it does not create a NOK sample.',
          'Needs review stays pending without overriding the traffic light.',
        ],
      },
    ],
    related: ['inspection-detail', 'glossary-feedback-verdict', 'faq-feedback-denied'],
  },
  {
    id: 'good-part-training',
    category: 'workflow',
    title: 'Good-part training in the dashboard',
    keywords: [
      'training',
      'good part',
      'i.o.',
      'model',
      'patchcore',
      'memory bank',
      'promote',
      'activate',
      'history',
    ],
    summary: 'Capture i.O. parts only, train, keep every run in history, and reactivate a previous training later.',
    screen: 'Configuration',
    sections: [
      {
        heading: 'Why good parts only?',
        paragraphs: [
          'AnomalyMatrix learns the nominal state from good-part (i.O.) references. Defective parts must not go into training.',
          'Without a real memory bank, scoring falls back to OpenCV/hash — shown as the Memory bank status. The heatmap is then a high-frequency residual, not a model overlay.',
          'Legacy image-level banks still load; retrain and promote once for a patch heatmap on the defect region.',
        ],
      },
      {
        heading: 'Flow on Configuration',
        paragraphs: [
          '1. Select the recipe and the camera (for example USB /dev/video0).',
          '2. Present good parts and use Capture good parts — PNGs are stored under training-images/{recipe}.',
          '3. Start training to create a candidate memory-bank .npz. Previous trainings are never deleted.',
          '4. After review, Promote (validation gate) or Activate (reuse a stored bank without retraining).',
          '5. Use Rollback or activate an older row in the history when you need to switch back.',
          '6. Run inspection → QA “Anomaly confirmed” marks NOK and stores a NOK sample (count in this panel).',
        ],
      },
      {
        heading: 'Permissions',
        paragraphs: [
          'Capture, train, promote, and activate: Process Engineer and Admin (models.train / models.promote).',
          'Operators can read history and the active model; action buttons stay disabled.',
        ],
      },
    ],
    related: ['configuration-overview', 'roles-overview', 'what-is-anomalymatrix'],
  },
  {
    id: 'engineer-trends-flow',
    category: 'workflow',
    title: 'Process engineer: interpreting trends',
    keywords: ['engineer', 'drift', 'process', 'trend', 'analysis'],
    summary: 'Recognize early warning signs of process drift.',
    sections: [
      {
        heading: 'Approach',
        paragraphs: [
          'Open the Trends screen and compare Average score and Anomaly count.',
          'If the average rises over several hours/shifts, review process parameters.',
          'Single spikes may be random — evaluate patterns over time.',
        ],
      },
      {
        heading: 'Coordination',
        paragraphs: [
          'For sustained trends: align with operator and QA on feedback history.',
          'Cross-check recipe and model version under Configuration.',
        ],
      },
    ],
    related: ['trends-overview', 'glossary-anomaly-score'],
  },
  {
    id: 'plc-opcua-signals',
    category: 'workflow',
    title: 'PLC integration (OPC UA)',
    keywords: ['plc', 'opc', 'stop', 'trigger', 'automatic', 'line'],
    summary: 'Trigger inspections from the PLC and stop the line on red.',
    sections: [
      {
        heading: 'Automatic inspection (PLC → software)',
        paragraphs: [
          'The PLC sets ExternalTrigger or StartRequest to TRUE (rising edge).',
          'AnomalyMatrix then runs an inspection automatically.',
          'Optionally set camera and recipe via Request.CameraId / Request.RecipeId.',
          'Alternative: call the OPC UA method StartInspection.',
        ],
      },
      {
        heading: 'Signals on red (software → PLC)',
        paragraphs: [
          'StopLineRequest = TRUE — request to stop the line.',
          'RejectPart = TRUE — request to reject the part.',
          'DecisionCode = 2 (red), PassFailBool = FALSE.',
          'ResultReady = TRUE when the result is complete.',
        ],
      },
      {
        heading: 'Acknowledge stop',
        paragraphs: [
          'After handling the stop, the PLC sets AcknowledgeStop to TRUE.',
          'AnomalyMatrix clears StopLineRequest and RejectPart.',
        ],
      },
      {
        heading: 'On green or amber',
        paragraphs: [
          'StopLineRequest and RejectPart remain FALSE.',
          'DecisionCode: 0 = green, 1 = amber.',
        ],
      },
    ],
    related: ['dashboard-kpis', 'decision-colors', 'operator-daily-flow'],
  },
  {
    id: 'dashboard-overview',
    category: 'screens',
    title: 'Dashboard',
    keywords: ['dashboard', 'pipeline', 'inspection', 'list', 'kpi'],
    summary: 'Starting point for inspections and overview of recent results.',
    screen: 'Dashboard',
    sections: [
      {
        heading: 'Header area',
        paragraphs: [
          'Shows line, active recipe, and model version.',
          'Status badge: overall state of the inspection station (e.g. ready / warning).',
        ],
      },
      {
        heading: 'Run Inspection Pipeline',
        paragraphs: [
          'Starts a full inspection (capture, evaluation, storage).',
          'While running: button shows "Running…" — do not click again.',
          'After completion: message with result (e.g. finished with GREEN/AMBER/RED).',
          '"Open Inspection Detail" jumps to the detail view of the selected inspection.',
        ],
      },
      {
        heading: 'Latest inspections',
        paragraphs: [
          'Chronological list: time, inspection ID, part/recipe, traffic-light decision.',
          'Click a row → Inspection Detail for that inspection.',
        ],
      },
    ],
    related: ['dashboard-kpis', 'decision-colors', 'pipeline-messages'],
  },
  {
    id: 'dashboard-kpis',
    category: 'decisions',
    title: 'Dashboard KPIs',
    keywords: ['kpi', 'cycle', 'anomaly rate', 'queue', 'opc'],
    summary: 'What the metrics mean for day-to-day operation.',
    sections: [
      {
        heading: 'Cycle p95',
        paragraphs: [
          '95th percentile of inspection cycle time in milliseconds.',
          'A significant rise may mean slower line response — notify maintenance.',
        ],
      },
      {
        heading: 'Anomaly Rate',
        paragraphs: [
          'Share of recent inspections with amber or red.',
          'High rate: monitor process or model more closely (Trends screen).',
        ],
      },
      {
        heading: 'Queue Lag',
        paragraphs: [
          'Wait time in the processing queue.',
          'High values may indicate load or a fault.',
        ],
      },
      {
        heading: 'OPC UA Error',
        paragraphs: [
          'Error rate when sending the inspection result to machine control.',
          'Non-zero: result may not have reached the PLC — have maintenance check.',
        ],
      },
    ],
    related: ['dashboard-overview', 'trends-overview'],
  },
  {
    id: 'inspection-detail',
    category: 'screens',
    title: 'Inspection Detail',
    keywords: ['detail', 'score', 'heatmap', 'pass', 'fail', 'review'],
    summary: 'View a single inspection in detail.',
    screen: 'Inspection Detail',
    sections: [
      {
        heading: 'Display',
        paragraphs: [
          'Inspection ID, part/recipe, and time of inspection.',
          'Anomaly score — numeric suspicion index (0 to 1, see Glossary).',
          'Defect label — system-suggested defect class or "none".',
          'Pass / Review / Fail — short decision as OK / Review / NOK.',
          'Model version and whether a trained memory bank is loaded.',
        ],
      },
      {
        heading: 'Heatmap',
        paragraphs: [
          'Shows anomaly intensity from the active model, relative to this recipe’s review/NOK thresholds — not auto-stretched per image. Regions well below the review threshold stay close to the raw image; around review they turn amber; at or above NOK they are hot red. Without a bank the overlay is a high-frequency residual, still gated by those thresholds, and is labeled as non-model.',
          'Image-level (legacy) banks still produce a model residual versus the nearest good-part embedding; retrain for patch-grid localization.',
          'For final judgment always compare the part and the image.',
        ],
      },
      {
        heading: 'No inspection selected?',
        paragraphs: [
          'First start an inspection on Dashboard or select a row under "Latest inspections".',
        ],
      },
    ],
    related: ['qa-review-flow', 'glossary-anomaly-score', 'faq-no-inspection'],
  },
  {
    id: 'trends-overview',
    category: 'screens',
    title: 'Trends',
    keywords: ['trends', 'average', 'history', 'samples'],
    summary: 'History and metrics across multiple inspections.',
    screen: 'Trends',
    sections: [
      {
        heading: 'Metrics',
        paragraphs: [
          'Average score — mean anomaly score in the selected period.',
          'Worst score — highest score (worst single result).',
          'Anomaly count — number of flagged inspections (red).',
          'Total samples — number of inspections included in the statistics.',
        ],
      },
      {
        heading: 'Latest trend points',
        paragraphs: [
          'List of recent individual values with time, ID, score, and decision.',
          'Source is shown (live statistics or local list).',
        ],
      },
      {
        heading: 'Traffic light next to average',
        paragraphs: [
          'Derived from Average score — same thresholds as single inspections.',
        ],
      },
    ],
    related: ['engineer-trends-flow', 'decision-colors'],
  },
  {
    id: 'configuration-overview',
    category: 'screens',
    title: 'Configuration',
    keywords: ['config', 'recipe', 'model', 'license', 'profile'],
    summary: 'Settings and status values shown on this screen.',
    screen: 'Configuration',
    sections: [
      {
        heading: 'Recipe & model',
        paragraphs: [
          'Recipe version — active inspection recipe (lighting, camera, limits).',
          'Recipes — create, edit, and delete with double confirmation (Process Engineer/Admin). Operators may read and select recipes on the Dashboard. recipe-default is protected.',
          'Model profile — which anomaly model is used for evaluation.',
          'Training / Models — capture good-part images, train PatchCore, promote candidates, and reactivate older trainings.',
          'Decision thresholds — OK / review / NOK sensitivity per recipe (Process Engineer/Admin).',
          'EOL station standard / Vision Setup — camera roles (top/side/bottom/STF), lens/FOV notes, lighting, and checklist. Export JSON/YAML or clone for another line.',
          'Storage & retention — object count, TTL, archive, watchdog for 24h operation. The last inspection EPC is shown on the Dashboard.',
          'NOK samples — count of QA-confirmed defect images (not mixed into good-part training).',
          'Only Process Engineer or Admin may train; operators can read the history.',
        ],
      },
      {
        heading: 'Integration',
        paragraphs: [
          'OPC UA profile — how results are reported to the line. MQTT triggers (PLC/MES) run in addition; both may be active.',
          'Audit mode — whether inspection and feedback actions are logged.',
        ],
      },
      {
        heading: 'License',
        paragraphs: [
          'License tier — licensed level.',
          'License active — whether the software may run inspections (if "false", notify your supervisor).',
          'Grace active — temporary tolerance without live license server.',
          'License & billing — administrators buy, renew, or cancel here via Stripe. Do not use the vendor license admin UI.',
        ],
      },
    ],
    related: ['license-status-user', 'roles-overview', 'good-part-training', 'eol-vision-setup'],
  },
  {
    id: 'eol-vision-setup',
    category: 'screens',
    title: 'EOL station standard (Vision Setup)',
    keywords: ['vision', 'eol', 'camera', 'bottom', 'epc', 'mqtt', 'retention', 'checklist', 'basler'],
    summary: 'Camera roles, optics notes, checklist, and a template for other lines.',
    screen: 'Configuration',
    sections: [
      {
        heading: 'What to fill in',
        paragraphs: [
          'Per slot: role (top, side, bottom, STF, completeness), lens/FOV notes, exposure, gain, trigger, and an optional light-controller hook.',
          'The perspective checklist (corners, edges, features, bottom view) is confirmed by the operator before go-live.',
          'Export JSON/YAML or clone the profile onto a new station ID — that is the copyable Phase-3 standard.',
        ],
      },
      {
        heading: 'EPC and triggers',
        paragraphs: [
          'Every capture is bound to an EPC (or process id) — shown on the Dashboard and Inspection Detail.',
          'The PLC may trigger via OPC UA or MQTT; both may run in parallel.',
        ],
      },
    ],
    related: ['configuration-overview', 'operator-daily-flow'],
  },
  {
    id: 'license-status-user',
    category: 'screens',
    title: 'Understanding license status',
    keywords: ['license', 'licensed', 'grace', 'active', 'billing', 'stripe', 'checkout'],
    summary: 'What the license display on Configuration means for you.',
    sections: [
      {
        heading: 'Licensed (active)',
        paragraphs: ['Inspections are enabled. No action required.'],
      },
      {
        heading: 'Unlicensed / not active',
        paragraphs: [
          'New inspections may be blocked.',
          'Notify your shift lead or supervisor — do not change system configuration yourself.',
        ],
      },
      {
        heading: 'Grace active',
        paragraphs: [
          'Short-term transition mode (e.g. network outage to license server).',
          'Operation may continue, but the condition should be resolved promptly.',
        ],
      },
    ],
    related: ['configuration-overview', 'faq-license-blocked'],
  },
  {
    id: 'roles-overview',
    category: 'roles',
    title: 'Roles — who can do what?',
    keywords: ['role', 'operator', 'qa', 'admin', 'permission'],
    summary: 'Overview of user roles in the interface.',
    sections: [
      {
        heading: 'Operator',
        paragraphs: [
          'Start inspections and view results.',
          'Read Dashboard, Detail (without feedback), Trends, and Configuration.',
        ],
      },
      {
        heading: 'QA Lead',
        paragraphs: [
          'Everything an Operator can do, plus QA feedback on Inspection Detail.',
          'Assessments for quality assurance and model improvement.',
        ],
      },
      {
        heading: 'Process Engineer',
        paragraphs: [
          'Analysis of trends, recipes, and models.',
          'On Configuration: capture good parts, train models, promote them, and reactivate older trainings.',
          'Read feedback; typically does not start new inspections on the line.',
        ],
      },
      {
        heading: 'Administrator',
        paragraphs: [
          'Full access including audit and system topics.',
          'Sets up roles and licenses — not an on-line operator task.',
        ],
      },
    ],
    related: ['qa-review-flow', 'faq-feedback-denied'],
  },
  {
    id: 'decision-colors',
    category: 'decisions',
    title: 'Traffic lights: OK, review, NOK',
    keywords: ['green', 'amber', 'red', 'pass', 'fail', 'ok', 'nok', 'i.o.'],
    summary: 'Meaning of OK (green), review (amber), and NOK (red).',
    sections: [
      {
        heading: 'Green — OK',
        paragraphs: [
          'No relevant anomaly suspicion. Part is OK.',
          'Continue production per plant standard.',
        ],
      },
      {
        heading: 'Amber — Review',
        paragraphs: [
          'Borderline — human re-check recommended.',
          'Do not automatically reject; follow QA rules.',
        ],
      },
      {
        heading: 'Red — NOK',
        paragraphs: [
          'Strong anomaly suspicion, defect class, or QA confirmation.',
          'Hold/rework the part per process; involve QA.',
        ],
      },
      {
        heading: 'Thresholds in the HMI',
        paragraphs: [
          'Defaults: review from 0.55, NOK from 0.85. Process Engineer/Admin set values per recipe under Configuration.',
          'QA “Anomaly confirmed” overrides the display to NOK regardless of score.',
        ],
      },
    ],
    related: ['glossary-anomaly-score', 'operator-daily-flow'],
  },
  {
    id: 'pipeline-messages',
    category: 'faq',
    title: 'Messages for "Run Inspection Pipeline"',
    keywords: ['pipeline', 'running', 'failed', 'message', 'status'],
    summary: 'What status messages after starting an inspection mean.',
    sections: [
      {
        heading: '"Pipeline running…"',
        paragraphs: ['Inspection in progress — wait until success or error is shown.'],
      },
      {
        heading: '"Inspection … completed (GREEN/AMBER/RED)"',
        paragraphs: ['Inspection successful. Result appears in the list and in Inspection Detail.'],
      },
      {
        heading: '"Pipeline failed …"',
        paragraphs: [
          'Inspection could not be completed.',
          'Check connection status at the top; try again.',
          'If the error persists: notify shift lead or maintenance — do not click repeatedly without coordination.',
        ],
      },
    ],
    related: ['faq-connection-offline', 'dashboard-overview'],
  },
  {
    id: 'faq-no-inspection',
    category: 'faq',
    title: '"No inspection selected"',
    keywords: ['none', 'selected', 'empty', 'detail'],
    summary: 'Inspection Detail with no inspection chosen.',
    sections: [
      {
        heading: 'Solution',
        paragraphs: [
          'Go to Dashboard.',
          'Run "Run Inspection Pipeline" or click a row in "Latest inspections".',
          'Then open Inspection Detail again.',
        ],
      },
    ],
    related: ['inspection-detail', 'operator-daily-flow'],
  },
  {
    id: 'faq-feedback-denied',
    category: 'faq',
    title: 'Cannot submit feedback',
    keywords: ['feedback', 'failed', 'permission', '403'],
    summary: 'Error message when submitting QA feedback.',
    sections: [
      {
        heading: 'Typical cause',
        paragraphs: [
          'Your user does not have the QA role (Operator only, or engineer without feedback rights).',
        ],
      },
      {
        heading: 'What to do',
        paragraphs: [
          'Ask a QA Lead or administrator to enter the feedback.',
          'For permanent access: ask an administrator to assign the "QA Lead" role.',
        ],
      },
    ],
    related: ['qa-review-flow', 'roles-overview'],
  },
  {
    id: 'faq-connection-offline',
    category: 'faq',
    title: '"Offline seed data" in the header',
    keywords: ['offline', 'connected', 'backend', 'connection'],
    summary: 'The interface shows no live connection.',
    sections: [
      {
        heading: 'Meaning',
        paragraphs: [
          'The display is using fallback/demo data.',
          'New inspections may not be possible or may not be persisted.',
        ],
      },
      {
        heading: 'What to do',
        paragraphs: [
          'Do not make production-critical decisions based on the display alone.',
          'Notify maintenance or your supervisor — have the connection to inspection software restored.',
        ],
      },
    ],
    related: ['pipeline-messages', 'hmi-overview'],
  },
  {
    id: 'faq-license-blocked',
    category: 'faq',
    title: 'Inspection will not start (license)',
    keywords: ['license', 'blocked', 'inspection', 'locked'],
    summary: 'Inspection button returns a license error.',
    sections: [
      {
        heading: 'Signs',
        paragraphs: [
          'Configuration shows License active: false.',
          'Pipeline message indicates a locked function.',
        ],
      },
      {
        heading: 'What to do',
        paragraphs: [
          'Notify shift lead and supervisor.',
          'An administrator can buy or renew the license on Configuration → License & billing (Stripe checkout inside AnomalyMatrix).',
        ],
      },
    ],
    related: ['license-status-user', 'configuration-overview'],
  },
  {
    id: 'glossary-anomaly-score',
    category: 'glossary',
    title: 'Anomaly score',
    keywords: ['score', 'value', 'number', 'threshold'],
    summary: 'Numeric suspicion index from 0 to 1.',
    sections: [
      {
        heading: 'Interpretation',
        paragraphs: [
          'The higher the value, the more the part deviates from the "good part" model.',
          'From the recipe threshold (default 0.55): Review (amber). From the NOK threshold (default 0.85): NOK (red). Below: OK (green).',
          'Process engineers set thresholds in Configuration — the traffic-light decision is authoritative.',
        ],
      },
    ],
    related: ['decision-colors', 'trends-overview'],
  },
  {
    id: 'glossary-inspection',
    category: 'glossary',
    title: 'Inspection',
    keywords: ['inspection', 'cycle', 'run'],
    summary: 'One complete automatic inspection cycle.',
    sections: [
      {
        heading: 'Process',
        paragraphs: [
          'Capture image → software evaluates → decision (green/amber/red) → storage.',
          'Result may be reported to machine control.',
        ],
      },
    ],
    related: ['dashboard-overview', 'operator-daily-flow'],
  },
  {
    id: 'glossary-feedback-verdict',
    category: 'glossary',
    title: 'Feedback verdicts',
    keywords: ['confirm', 'false positive', 'recheck', 'verdict'],
    summary: 'Your QA classification after the inspection.',
    sections: [
      {
        heading: 'Confirm anomaly',
        paragraphs: [
          'The system was correct — real defect. The inspection is shown as NOK and the image is stored as a NOK sample.',
        ],
      },
      {
        heading: 'False positive',
        paragraphs: ['The part is OK — the software raised a false alarm.'],
      },
      {
        heading: 'Re-check required',
        paragraphs: ['Still unclear — further analysis by QA or lab required.'],
      },
    ],
    related: ['qa-review-flow', 'inspection-detail'],
  },
  {
    id: 'glossary-recipe',
    category: 'glossary',
    title: 'Recipe',
    keywords: ['recipe', 'version', 'camera'],
    summary: 'Inspection specification for a part at the current station.',
    sections: [
      {
        heading: 'Typically includes',
        paragraphs: [
          'Camera and lighting settings.',
          'Assigned anomaly model and limits.',
          'Maintained under Configuration (Process Engineer/Admin). Operators select the recipe on the Dashboard.',
        ],
      },
    ],
    related: ['configuration-overview'],
  },
];
