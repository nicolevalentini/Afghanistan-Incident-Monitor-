# Afghanistan-Incident-Monitor-

Web-based tool for monitoring and documenting security incidents and human rights violations in Afghanistan, including attacks, bombings, killings, floggings, and executions.

About

This tool aggregates RSS feeds from 20 news sources in three languages, English, Farsi/Dari, and Pashto, and presents relevant articles for daily human review. A reviewer reads each article, fills in structured data fields, and exports the results as a CSV file ready to open in Excel.

It is developed and maintained by Nicole Valentini. 

 How it works

1. The tool fetches the latest articles from 20 RSS feeds simultaneously
2. Articles are automatically filtered by incident-related keywords in English, Farsi, and Pashto
3. A reviewer goes through each article, fills in structured fields (location, province, attack type, perpetrator, target, casualties), and marks it as verified or dismisses it as irrelevant
4. Verified incidents are exported to a CSV file

 Sources monitored

| Source | Language |
|---|---|
| TOLOnews | English, Farsi, Pashto |
| Pajhwok | English, Farsi, Pashto |
| Khaama Press | English |
| Ariana News | English |
| Zan Times | English |
| Afghan Analysts Network | English |
| Roshana | English |
| Afghanistan International | English, Farsi |
| BBC World | English |
| Reuters | English |
| BBC فارسی | Farsi |
| رادیو آزادی — RFE/RL | Farsi, Pashto |

Access

This is the frontend only. To use the tool, open `index.html` in any browser (Chrome, Firefox, or Edge).

The backend is hosted separately and handles all RSS fetching server-side.

License

This project is for internal and humanitarian use. Please contact nicolevalentini@protonmail.com before reusing or adapting this tool.
