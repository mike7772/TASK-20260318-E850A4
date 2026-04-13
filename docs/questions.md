# Questions.md

### 1
**question:** Role-based permissions are not clearly defined  
**assumption:** Each role has isolated responsibilities with minimal overlap  
**solution:** Define an explicit RBAC matrix (CRUD per entity per role) and enforce it via middleware in FastAPI

---

### 2  
**question:** Workflow state transitions are unclear  
**assumption:** The workflow is a strict finite state machine  
**solution:** Define allowed transitions explicitly (e.g., Submitted → Supplemented → Approved/Rejected) and enforce via backend validation logic

---


### 3  
**question:** Supplementary submission timing (72 hours) is ambiguous  
**assumption:** The 72-hour window starts after a “Needs Correction” or “Rejected” status  
**solution:** Store timestamp of triggering event and enforce a strict expiration check on supplementary submission endpoint

---

### 4  
**question:** File versioning limit (3 versions) lacks behavior definition  
**assumption:** Only the latest 3 versions should be retained  
**solution:** Implement FIFO replacement (delete oldest version when uploading the 4th)

---

### 5  
**question:** File upload conflict handling is not defined  
**assumption:** Concurrent uploads may happen  
**solution:** Use file-level locking or transactional upload handling to prevent corruption

---

### 6  
**question:** Batch review behavior is unclear  
**assumption:** Batch operations apply actions individually, not atomically  
**solution:** Process batch items independently with per-item success/failure reporting

---

### 7  
**question:** Financial overspending rule lacks calculation details  
**assumption:** Overspending is based on total allocated budget per activity  
**solution:** Compute cumulative expenses and trigger warning when >110% of budget before commit

---

### 8  
**question:** Similarity/duplicate check behavior is unclear  
**assumption:** Only file hash comparison is needed initially  
**solution:** Implement SHA-256 hash comparison and keep interface extensible for future logic

---

### 9  
**question:** Authentication/session management is not defined  
**assumption:** System uses token-based authentication  
**solution:** Implement JWT-based authentication with refresh tokens

---

### 10  
**question:** Recovery process is not defined  
**assumption:** Full restore is acceptable  
**solution:** Provide CLI or UI-triggered restore from backup files

---


### 11  
**question:** Concurrency handling is not addressed  
**assumption:** Multiple users may edit simultaneously  
**solution:** Use optimistic locking (version/timestamp checks)

---


### 12  
**question:** Timezone handling is not specified  
**assumption:** System operates in a single timezone  
**solution:** Use UTC internally and convert to local timezone in UI

---

