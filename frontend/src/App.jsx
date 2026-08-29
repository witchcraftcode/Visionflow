*{
  margin:0;
  padding:0;
  box-sizing:border-box;
}

body{
  font-family:Inter,system-ui,sans-serif;
  background:#08101b;
  color:#f8fafc;
}

a{
  color:inherit;
  text-decoration:none;
}

.app{
  min-height:100vh;
  background:
    radial-gradient(circle at top,#0f2b52 0%,#08101b 55%);
}

.container{
  width:min(1200px,92%);
  margin:auto;
  padding:32px 0 60px;
}

/* NAVBAR */

.nav{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:20px 4%;
  border-bottom:1px solid rgba(255,255,255,.08);
  backdrop-filter:blur(18px);
}

.logo{
  display:flex;
  align-items:center;
  gap:12px;
  font-weight:700;
  font-size:20px;
}

.logo-dot{
  width:14px;
  height:14px;
  border-radius:50%;
  background:#3b82f6;
  box-shadow:0 0 18px #3b82f6;
}

.nav-links{
  display:flex;
  gap:26px;
  color:#cbd5e1;
  font-size:15px;
}

.nav-links a:hover{
  color:#fff;
}

/* HERO */

.hero{
  margin-top:32px;
  background:linear-gradient(135deg,#111827,#0f172a);
  border:1px solid rgba(255,255,255,.08);
  border-radius:24px;
  padding:48px;
}

.badge{
  display:inline-block;
  background:#2563eb;
  color:#fff;
  padding:6px 14px;
  border-radius:999px;
  font-size:12px;
  letter-spacing:.5px;
  margin-bottom:18px;
}

.hero h1{
  font-size:56px;
  line-height:1.05;
  margin-bottom:16px;
}

.hero p{
  color:#cbd5e1;
  max-width:760px;
  line-height:1.7;
  font-size:18px;
}

.hero-tags{
  display:flex;
  flex-wrap:wrap;
  gap:12px;
  margin-top:28px;
}

.hero-tags span{
  background:#1e293b;
  border:1px solid rgba(255,255,255,.06);
  color:#93c5fd;
  padding:8px 14px;
  border-radius:999px;
  font-size:13px;
}

/* STATS */

.stats-grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:18px;
  margin:28px 0 40px;
}

.stat-card{
  background:#111827;
  border:1px solid rgba(255,255,255,.08);
  border-radius:18px;
  padding:22px;
}

.stat-card p{
  color:#94a3b8;
  font-size:13px;
}

.stat-card h2{
  font-size:34px;
  margin:10px 0;
}

.stat-card span{
  color:#64748b;
  font-size:13px;
}

/* SECTION */

.section{
  margin-top:42px;
}

.section-title{
  margin-bottom:20px;
}

.section-title h2{
  font-size:30px;
  margin-bottom:6px;
}

.section-title p{
  color:#94a3b8;
}

/* MODELS */

.models{
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:18px;
}

.model-card{
  background:#111827;
  border:1px solid rgba(255,255,255,.08);
  border-radius:18px;
  padding:22px;
  cursor:pointer;
  transition:.25s;
}

.model-card:hover{
  transform:translateY(-4px);
}

.model-card.active{
  border:1px solid #3b82f6;
  background:#13213d;
}

.model-card h3{
  margin-top:10px;
}

.model-card p{
  color:#94a3b8;
  margin-top:8px;
  font-size:14px;
}

/* WORKSPACE */

.workspace{
  display:grid;
  grid-template-columns:1.15fr .85fr;
  gap:24px;
  margin-top:26px;
}

.upload-card,
.result-card{
  background:#111827;
  border:1px solid rgba(255,255,255,.08);
  border-radius:22px;
  padding:24px;
}

.upload-card h2,
.result-card h2{
  margin-bottom:18px;
}

.dropzone{
  border:2px dashed #334155;
  border-radius:16px;
  padding:36px;
  text-align:center;
  transition:.2s;
}

.dropzone:hover{
  border-color:#3b82f6;
}

.dropzone input{
  display:none;
}

.upload-btn{
  display:inline-block;
  background:#2563eb;
  padding:12px 22px;
  border-radius:10px;
  cursor:pointer;
  font-weight:600;
}

.file-preview{
  margin-top:20px;
  border-radius:14px;
  overflow:hidden;
}

.file-preview img{
  width:100%;
  display:block;
}

.file-info{
  display:flex;
  justify-content:space-between;
  margin-top:12px;
  color:#94a3b8;
  font-size:14px;
}

.predict-btn{
  width:100%;
  margin-top:22px;
  border:none;
  background:#2563eb;
  color:white;
  padding:14px;
  border-radius:12px;
  font-size:16px;
  font-weight:700;
  cursor:pointer;
}

.predict-btn:hover{
  background:#1d4ed8;
}

/* RESULT */

.status-pill{
  display:inline-block;
  padding:7px 14px;
  border-radius:999px;
  background:#1e293b;
  color:#93c5fd;
  font-size:13px;
  margin-bottom:18px;
}

.result-main{
  text-align:center;
  padding:20px 0;
}

.result-main h1{
  font-size:44px;
  margin:8px 0;
}

.confidence{
  color:#22c55e;
  font-weight:700;
  font-size:22px;
}

.meta{
  margin-top:24px;
  display:grid;
  gap:14px;
}

.meta-row{
  display:flex;
  justify-content:space-between;
  color:#cbd5e1;
  font-size:14px;
}

.progress{
  width:100%;
  height:10px;
  background:#1e293b;
  border-radius:999px;
  overflow:hidden;
  margin-top:12px;
}

.progress-fill{
  height:100%;
  background:linear-gradient(90deg,#2563eb,#22c55e);
}

/* ARCHITECTURE */

.architecture{
  display:grid;
  grid-template-columns:repeat(6,1fr);
  gap:12px;
}

.node{
  background:#111827;
  border:1px solid rgba(255,255,255,.08);
  border-radius:16px;
  padding:16px;
  text-align:center;
}

.node h4{
  font-size:14px;
  margin-top:10px;
}

.node p{
  color:#94a3b8;
  font-size:12px;
  margin-top:6px;
}

/* FOOTER */

.footer{
  margin-top:48px;
  border-top:1px solid rgba(255,255,255,.08);
  padding-top:24px;
  display:flex;
  justify-content:space-between;
  color:#64748b;
  font-size:14px;
}

/* MOBILE */

@media (max-width:960px){

  .stats-grid,
  .models,
  .workspace,
  .architecture{
    grid-template-columns:1fr;
  }

  .hero{
    padding:30px;
  }

  .hero h1{
    font-size:40px;
  }

  .footer{
    flex-direction:column;
    gap:10px;
  }
}