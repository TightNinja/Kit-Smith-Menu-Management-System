# Kit-Smith Menu Engineering & Procurement System

An enterprise-grade menu engineering platform that handles algorithmic hospitality data parsing, cost-yield analytics, and permanent SQL storage matrices.

## 🛠️ Architecture Stack
* **Frontend UI:** Interactive HTML5 / Tailwind CSS Data Dashboard
* **Application Controller:** Python / Flask Web Server
* **Database Engine:** Relational SQLite Database Model
* **Data Processing Layer:** Pandas Pipeline for automated package/matrix parsing

## 📊 Core Features & Business Logic
* **Dynamic Package Unboxing:** Automatically unpacks and evaluates multi-unit vendor variables (e.g., handles string schemas like `12/1 QT` and `36/1 LB` down to pure unit costs).
* **Trim & Yield Factor Logic:** Computes raw cost vs. true usable product cost to protect margins from food item shrinkage and kitchen production waste.
* **Menu Engineering Matrix:** Relational multi-table SQL `JOIN` mapping that calculates dynamic retail suggestions and projected gross profit margins based on target food cost thresholds.
* **Portfolio Security Isolation:** Configured with robust `.gitignore` layers to process mock data environments locally without leaking backend information databases.
