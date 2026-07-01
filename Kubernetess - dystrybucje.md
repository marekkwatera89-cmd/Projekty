# Porównanie dystrybucji Kubernetes – K3s vs MicroK8s vs Vanilla Kubernetes

> Praktyczne porównanie trzech najpopularniejszych dystrybucji Kubernetes z uwzględnieniem wymagań sprzętowych, architektury, kosztów wdrożenia, czasu implementacji oraz zastosowań.

---

# Spis treści

1. Wstęp
2. Czym są poszczególne dystrybucje?
3. Architektura i wymagania infrastrukturalne
4. Porównanie zasobów
5. Czas i koszt wdrożenia
6. Zalety i wady
7. Kiedy wybrać daną dystrybucję?
8. Podsumowanie

---

# Wstęp

Kubernetes jest obecnie najpopularniejszą platformą do orkiestracji kontenerów. Oprócz oficjalnej dystrybucji (Vanilla Kubernetes) dostępne są również lżejsze rozwiązania, takie jak **K3s** oraz **MicroK8s**.

Wszystkie trzy dystrybucje są zgodne z API Kubernetes, jednak różnią się:

- wymaganiami sprzętowymi,
- stopniem skomplikowania wdrożenia,
- kosztami utrzymania,
- czasem konfiguracji,
- docelowym zastosowaniem.

---

# Czym są poszczególne dystrybucje?

## Vanilla Kubernetes

Oficjalna implementacja rozwijana przez społeczność Kubernetes (CNCF). Administrator sam dobiera wszystkie komponenty, takie jak sieć, storage, monitoring czy Ingress.

**Najlepiej sprawdza się w:**

- dużych środowiskach produkcyjnych,
- centrach danych,
- chmurach prywatnych,
- środowiskach Enterprise.

---

## K3s

Lekka dystrybucja opracowana przez Rancher.

Najważniejsze cechy:

- bardzo małe wymagania sprzętowe,
- szybka instalacja,
- wbudowany Traefik,
- wbudowany ServiceLB,
- możliwość pracy na Raspberry Pi i Edge.

Instalacja:

```bash
curl -sfL https://get.k3s.io | sh -
```

---

## MicroK8s

Dystrybucja rozwijana przez Canonical.

Najważniejsze cechy:

- prostota instalacji,
- modułowe dodatki,
- bardzo dobra integracja z Ubuntu.

Instalacja:

```bash
sudo snap install microk8s --classic
```

---

# Architektura i wymagania infrastrukturalne

Największą różnicą pomiędzy tymi rozwiązaniami jest liczba wymaganych komponentów do uruchomienia klastra.

## K3s

Już jedna maszyna może stanowić kompletny klaster.

```text
+----------------------+
| VM 1                 |
|----------------------|
| Control Plane        |
| Worker               |
| SQLite / etcd        |
| Traefik              |
| ServiceLB            |
+----------------------+
```

Świetny wybór do:

- HomeLab
- środowisk developerskich
- testów
- małych środowisk produkcyjnych

---

## MicroK8s

Również może działać na jednej maszynie.

```text
+----------------------+
| VM 1                 |
|----------------------|
| Control Plane        |
| Worker               |
| Add-ons              |
+----------------------+
```

Najczęściej wykorzystywany przez programistów oraz w środowiskach testowych.

---

## Vanilla Kubernetes

Produkcyjne wdrożenia zazwyczaj wymagają architektury HA.

```text
                 +-----------+
                 | HAProxy   |
                 +-----+-----+
                       |
        +--------------+--------------+
        |              |              |
+---------------+ +---------------+ +---------------+
| ControlPlane1 | | ControlPlane2 | | ControlPlane3 |
+---------------+ +---------------+ +---------------+
        |              |              |
        +--------------+--------------+
                       |
                Worker Nodes
                       |
        +------------------------------+
        | NFS / Ceph / SAN / Longhorn |
        +------------------------------+
```

Najczęściej wymagane komponenty:

- 3 × Control Plane,
- HAProxy lub Keepalived,
- magazyn danych (NFS, Ceph, SAN lub Longhorn),
- Ingress Controller,
- cert-manager,
- monitoring (Prometheus + Grafana),
- centralne logowanie (Loki/OpenSearch/Elasticsearch).

---

# Porównanie infrastruktury

| Element | K3s | MicroK8s | Vanilla |
|---------|-----|----------|----------|
| Minimalna liczba VM | 1 | 1 | 3–5 |
| Control Plane | 1 | 1 | 3 |
| Worker | opcjonalny | opcjonalny | osobne węzły |
| Load Balancer | ❌ | ❌ | ✅ |
| HAProxy | ❌ | ❌ | ✅ |
| Storage NFS/Ceph | opcjonalnie | opcjonalnie | zalecane |
| Traefik | wbudowany | add-on | instalacja ręczna |
| etcd | wbudowane | wbudowane | konfiguracja ręczna |

---

# Zużycie zasobów

| Dystrybucja | RAM | CPU |
|-------------|-----|-----|
| K3s | 500–800 MB | Bardzo niskie |
| MicroK8s | 1,5–2,5 GB | Średnie |
| Vanilla Kubernetes | 2–4 GB | Średnie |

K3s jest zdecydowanie najbardziej oszczędny pod względem zasobów.

---

# Czas wdrożenia

| Zadanie | K3s | MicroK8s | Vanilla |
|----------|-----|----------|----------|
| Instalacja | 5–15 min | 10–30 min | 1–2 h |
| Konfiguracja HA | 20–30 min | 1–2 h | 1–3 dni |
| Środowisko produkcyjne | kilka godzin | ok. 1 dzień | kilka dni |

---

# Koszt wdrożenia

| Dystrybucja | Minimalna infrastruktura | Szacowany koszt |
|-------------|--------------------------|-----------------|
| K3s | 1 × VM | ⭐ |
| MicroK8s | 1 × VM | ⭐⭐ |
| Vanilla | 3 × Control Plane + Workery + HAProxy + Storage | ⭐⭐⭐⭐⭐ |

Największy koszt Vanilla Kubernetes wynika nie tylko z liczby maszyn, ale również z czasu potrzebnego na konfigurację wszystkich komponentów.

---

# Zalety i wady

| Dystrybucja | Zalety | Wady |
|-------------|---------|------|
| K3s | Najmniejsze wymagania, szybka instalacja, niski koszt | Mniej opcji domyślnych dla dużych środowisk |
| MicroK8s | Prosta obsługa, Ubuntu, add-ons | Snap, większe wymagania niż K3s |
| Vanilla | Maksymalna elastyczność, standard Enterprise | Najbardziej skomplikowane wdrożenie |

---

# Kiedy wybrać daną dystrybucję?

| Scenariusz | Najlepszy wybór |
|------------|-----------------|
| HomeLab | 🥇 K3s |
| Raspberry Pi | 🥇 K3s |
| Edge Computing | 🥇 K3s |
| CI/CD | 🥇 K3s |
| Laptop programisty | 🥇 MicroK8s |
| Ubuntu Desktop | 🥇 MicroK8s |
| VMware | 🥇 Vanilla |
| OpenStack | 🥇 Vanilla |
| Enterprise | 🥇 Vanilla |
| Chmura prywatna | 🥇 Vanilla |

---

# Podsumowanie

Nie istnieje jedna uniwersalnie najlepsza dystrybucja Kubernetes.

- **K3s** będzie najlepszym wyborem, jeśli zależy nam na szybkim wdrożeniu, niskich kosztach oraz niewielkim zużyciu zasobów. W wielu przypadkach do uruchomienia klastra wystarczy pojedyncza maszyna wirtualna.

- **MicroK8s** jest dobrym rozwiązaniem dla programistów oraz użytkowników Ubuntu, którzy potrzebują prostego środowiska testowego lub developerskiego.

- **Vanilla Kubernetes** pozostaje najlepszym wyborem dla dużych środowisk produkcyjnych, gdzie wymagane są wysoka dostępność, pełna kontrola nad konfiguracją oraz integracja z rozbudowaną infrastrukturą.

> **Wniosek:** Jeżeli  budujesz niewielkie środowisko, wybierz **K3s**. Jeśli tworzysz dużą platformę dla przedsiębiorstwa, gdzie liczy się pełna kontrola i skalowalność, postaw na **Vanilla Kubernetes**.
