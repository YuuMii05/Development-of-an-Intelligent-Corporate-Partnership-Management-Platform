# Plateforme Intelligente de Gestion des Partenariats Huawei

> Moteur de matching sémantique propulsé par l'IA pour aligner les besoins clients
> avec les partenaires Huawei les plus pertinents en Tunisie.

---

## Concept du projet

Cette plateforme aide les équipes commerciales de **Huawei** à identifier, en temps réel,
le **meilleur partenaire intégrateur** capable de répondre à un besoin client donné.

Au lieu d'une simple recherche par mots-clés, le système utilise la **recherche vectorielle
sémantique** : il comprend le *sens* d'une demande (ex. « infrastructure de stockage cloud et
communication de données ») et la compare mathématiquement aux capacités réelles de chaque
partenaire.

Pour chaque partenaire identifié, l'application :

1. **Calcule un score de similarité** entre le besoin et le profil du partenaire ;
2. **Affiche des indicateurs stratégiques** : santé du partenariat, niveau de risque,
   tendance d'engagement, valeur future estimée ;
3. **Génère un diagnostic d'alignement** rédigé par une IA, en streaming, mot par mot ;
4. **Produit automatiquement une proposition commerciale B2B** formelle prête à l'envoi.

---

## Architecture & fonctionnement

```
┌──────────────┐    requête client      ┌─────────────────────┐
│  index.html  │ ───────────────────►   │   FastAPI (app.py)  │
│  (interface) │ ◄───── streaming ────  │                     │
└──────────────┘   (SSE temps réel)     └──────────┬──────────┘
                                                    │
                       ┌────────────────────────────┼───────────────────────┐
                       ▼                            ▼                       ▼
              ┌─────────────────┐         ┌────────────────────┐   ┌──────────────────┐
              │     Ollama      │         │      Supabase      │   │     Ollama       │
              │ nomic-embed-text│         │  (PostgreSQL +     │   │     llama3       │
              │  → vecteur 768  │         │   pgvector)        │   │ → texte généré   │
              └─────────────────┘         │  fonction RPC      │   └──────────────────┘
                 (embeddings)             │  match_partners    │     (diagnostics +
                                          └────────────────────┘      propositions)
```

### Étapes d'une recherche

1. L'utilisateur saisit un besoin client dans l'interface.
2. Le backend transforme cette phrase en **vecteur de 768 dimensions** via le modèle local
   `nomic-embed-text` (Ollama).
3. Ce vecteur est envoyé à Supabase, qui exécute la fonction SQL **`match_partners`** :
   elle calcule la **similarité cosinus** entre la requête et les embeddings des partenaires
   stockés, et renvoie les meilleurs résultats.
4. Les partenaires correspondants sont renvoyés à l'interface, puis le modèle `llama3`
   génère un **diagnostic stratégique** pour chacun, diffusé en **streaming (SSE)**.
5. Sur demande, une **proposition de partenariat** complète est générée.

---

## Stack technique

| Couche            | Technologie                                              |
|-------------------|---------------------------------------------------------|
| **Backend**       | Python · FastAPI · Uvicorn                              |
| **Base de données** | Supabase (PostgreSQL 17 + extension `pgvector`)       |
| **IA / Embeddings** | Ollama — `nomic-embed-text` (vecteurs 768 dimensions) |
| **IA générative** | Ollama — `llama3`                                       |
| **Streaming**     | Server-Sent Events (`sse-starlette`)                    |
| **Frontend**      | HTML / CSS / JavaScript (page unique `index.html`)      |
| **Config**        | `python-dotenv` (fichier `.env`)                        |

---

## Structure du projet

```
partner-backend/
├── app.py              # Application FastAPI (point d'entrée principal)
├── seed_partners.py    # Script d'initialisation : insère les partenaires + embeddings
├── index.html          # Interface utilisateur complète
├── .env                # Variables secrètes (NON versionné)
├── logo.jpg / lp1.jpg  # Ressources visuelles
└── requirements.txt    # Dépendances Python
```

### Base de données — table `partner_profiles`

| Colonne                  | Type          | Description                              |
|--------------------------|---------------|------------------------------------------|
| `id`                     | `bigint`      | Identifiant unique                       |
| `company_name`           | `text`        | Nom du partenaire                        |
| `industry`               | `text`        | Secteur d'activité                       |
| `objectives`             | `text`        | Capacités et spécialisations             |
| `embedding`              | `vector(768)` | Vecteur sémantique généré par l'IA       |
| `health_score`           | `integer`     | Score de santé du partenariat (0–100)    |
| `risk_level`             | `text`        | Niveau de risque (Low / Medium / High)   |
| `engagement_trend`       | `text`        | Tendance d'engagement                    |
| `future_value_estimate`  | `text`        | Valeur future estimée                    |

---

## Installation & lancement

### Prérequis

- **Python 3.10+**
- **Ollama** installé et lancé, avec les deux modèles :
  ```bash
  ollama pull nomic-embed-text
  ollama pull llama3
  ```
- Un projet **Supabase** avec la table `partner_profiles` et la fonction `match_partners`.

### 1. Configurer l'environnement

Créer un fichier `.env` à la racine :

```env
SUPABASE_URL="https://<votre-projet>.supabase.co"
SUPABASE_SERVICE_KEY="<votre-clé-supabase>"
```

> Le domaine se termine bien par **`.co`** (et non `.com`).

### 2. Installer les dépendances

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 3. Initialiser la base (une seule fois)

```bash
python seed_partners.py
```

Ce script vide la table, génère un embedding pour chaque partenaire via Ollama,
puis insère les profils dans Supabase.

### 4. Lancer l'application

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Puis ouvrir **http://127.0.0.1:8000**

---

## 🔌 Points d'entrée de l'API

| Méthode | Route                 | Description                                                       |
|---------|-----------------------|-------------------------------------------------------------------|
| `GET`   | `/`                   | Sert l'interface utilisateur (`index.html`)                       |
| `GET`   | `/stream-match`       | Recherche sémantique + diagnostic IA en streaming (SSE)           |
| `POST`  | `/generate-proposal`  | Génère une proposition de partenariat B2B formelle                |

**Exemple — `/stream-match`**

```
GET /stream-match?query=infrastructure de stockage cloud
```

Événements SSE renvoyés :
- `initial_matches` — la liste des partenaires correspondants ;
- `ai_chunk` — fragments du diagnostic IA, en temps réel ;
- `done` — fin du flux.

---

## Sécurité

- Les clés et URL sont chargées depuis `.env` (jamais codées en dur dans le code).
- Le fichier `.env` est ignoré par Git (`.gitignore`).
- **Recommandation production** : activer le *Row Level Security (RLS)* sur la table
  `partner_profiles` avec des politiques de lecture, puis utiliser une clé *secret* dédiée
  côté serveur.

---

## État du projet

Connexion Supabase fonctionnelle (recherche vectorielle opérationnelle)
Embeddings et matching sémantique validés (7 partenaires de référence)
Diagnostics IA en streaming temps réel
Génération automatique de propositions commerciales
Interface : liste des partenaires avec fiches « Profil » et « Contact »

---

*Projet : Développement d'une plateforme intelligente de gestion des partenariats d'entreprise.*
