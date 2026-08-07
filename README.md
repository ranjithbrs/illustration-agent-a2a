# Illustration Agent A2A

## 🎯 Overview
This project is part of the **Google Cloud Technical Series: Agentic AI Edition (GENAI120)**.  
It demonstrates how to build, deploy, and connect AI agents using the **Google Agent Development Kit (ADK)** and the **Agent‑to‑Agent (A2A) SDK**.  
The agent generates branded illustrations and is deployed on **Google Cloud Run** as a reusable A2A service.

## 🧩 Tasks Completed
1. **Install ADK and set up environment**  
   - Installed `google-adk[a2a]==1.31.0`  
   - Configured `.env` with project, region, and Gemini models  

2. **Explore the ADK agent locally**  
   - Tested the illustration agent in the Dev UI  
   - Verified brand guideline enforcement  

3. **Deploy the agent as an A2A Server**  
   - Deployed to Cloud Run with service account authentication  
   - Example output:  
     ```
     Service [illustration-agent] revision [illustration-agent-00001-cmf] has been deployed and is serving 100 percent of traffic.
     Service URL: https://illustration-agent-275456095190.us-east4.run.app
     ```

4. **Enable another ADK agent to call this agent remotely**  
   - Verified remote connectivity and successful A2A communication  
   - Lab validator confirmed completion with **100/100**

## ⚙️ Tech Stack
- Google Cloud Run  
- Google Agent Development Kit (ADK)  
- Agent‑to‑Agent (A2A) SDK  
- Python  
- Vertex AI (Gemini models)

## 🚀 Outcome
- Successfully deployed illustration agent as a Cloud Run service  
- Remote agents can query it via A2A protocol  
- Lab completion: **100/100**

## 📸 Screenshots
(Add your lab completion screenshot here for proof)

## 🧑‍💻 Author
**Ranjith**  
B.Tech CSBS Student, Nehru Institute of Engineering and Technology  
GitHub: [ranjithbrs](https://github.com/ranjithbrs)  
LinkedIn: [your-linkedin-profile]
