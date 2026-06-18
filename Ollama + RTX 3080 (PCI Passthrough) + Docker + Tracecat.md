 
Cel

Uruchomienie lokalnego LLM (Ollama) z wykorzystaniem dwóch kart NVIDIA RTX 3080 przekazanych do maszyny wirtualnej przez PCI Passthrough oraz integracja z Tracecat.

Środowisko
Host
KVM / Proxmox
PCI Passthrough GPU
VM
Ubuntu 24.04
16 vCPU
64 GB RAM
2× NVIDIA GeForce RTX 3080 (10 GB)
Weryfikacja wykrycia GPU

Sprawdzenie urządzeń PCI:

lspci | grep -i vga

Wynik:

00:10.0 VGA compatible controller: NVIDIA Corporation GA102 [GeForce RTX 3080]
00:11.0 VGA compatible controller: NVIDIA Corporation GA102 [GeForce RTX 3080]

Po instalacji sterowników NVIDIA:

nvidia-smi

Wynik:

Driver Version: 580.159.03
CUDA Version: 13.0

GPU 0 NVIDIA GeForce RTX 3080
GPU 1 NVIDIA GeForce RTX 3080
Instalacja NVIDIA Container Toolkit

Początkowo Docker nie widział GPU:

failed to discover GPU vendor from CDI: no known GPU vendor found

Instalacja:

apt update
apt install -y nvidia-container-toolkit

Konfiguracja Dockera:

nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

Weryfikacja:

docker info | grep -i runtime

Oczekiwany wynik:

Runtimes: io.containerd.runc.v2 nvidia runc
Test GPU w Dockerze
docker run --rm --gpus all \
nvidia/cuda:12.9.0-base-ubuntu24.04 \
nvidia-smi

Obie karty zostały poprawnie wykryte wewnątrz kontenera.

Docker Compose dla Ollama
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped

    ports:
      - "11434:11434"

    volumes:
      - ollama-data:/root/.ollama

    environment:
      NVIDIA_VISIBLE_DEVICES: all
      NVIDIA_DRIVER_CAPABILITIES: compute,utility

    runtime: nvidia

  ollama-exporter:
    image: lucabecker42/ollama-exporter:latest
    container_name: ollama-exporter
    restart: unless-stopped

    ports:
      - "8000:8000"

    environment:
      OLLAMA_HOST: http://ollama:11434

    depends_on:
      - ollama

volumes:
  ollama-data:

Uruchomienie:

docker compose up -d
Pobranie modeli
Llama 3.3
docker exec -it ollama ollama pull llama3.3

Rozmiar:

42 GB
Qwen3 14B
docker exec -it ollama ollama pull qwen3:14b

Rozmiar:

9.9 GB
Test API

Lista modeli:

curl http://localhost:11434/api/tags

Generowanie odpowiedzi:

curl http://localhost:11434/api/generate \
-d '{
  "model":"qwen3:14b",
  "prompt":"Co to jest SOC?",
  "stream":false
}'
Weryfikacja wykorzystania GPU

Sprawdzenie aktywnych modeli:

docker exec -it ollama ollama ps

Wynik:

NAME         ID              SIZE      PROCESSOR
qwen3:14b    bdbd181c33f2    9.9 GB    100% GPU

Monitorowanie:

watch -n1 nvidia-smi

W trakcie pracy:

GPU0: ~4.8 GB VRAM
GPU1: ~5.0 GB VRAM

Proces:

/usr/lib/ollama/llama-server

widoczny był na obu kartach.

Wydajność modeli
Llama 3.3 (70B)

Rozmiar:

42 GB

Wynik:

nie mieści się w 20 GB VRAM
duża część modelu trafia do RAM
około 0.7 tokena/s
odpowiedzi trwają kilka minut
Qwen3 14B

Rozmiar:

9.9 GB

Wynik:

działa w 100% na GPU
około 10–12 tokenów/s
odpowiedzi około 6 sekund po załadowaniu modelu

Przykład:

real    0m6.319s
Integracja z Tracecat
HTTP Request

Metoda:

POST

URL:

http://<OLLAMA_IP>:11434/api/generate

Payload:

model: qwen3:14b
prompt: Co to jest SOC?
stream: false
Problem: ReadTimeout

Tracecat zwracał:

ReadTimeout

Przyczyną nie był problem z komunikacją.

Tracecat poprawnie łączył się z Ollamą, jednak oczekiwał odpowiedzi krócej niż trwała inferencja modelu.

Weryfikacja połączenia:

GET http://<OLLAMA_IP>:11434/api/tags

Jeżeli endpoint zwraca listę modeli, komunikacja działa poprawnie.

Wnioski

Udało się:

skonfigurować PCI Passthrough dla 2× RTX 3080
uruchomić sterowniki NVIDIA i CUDA
skonfigurować NVIDIA Container Toolkit
udostępnić GPU do Dockera
uruchomić Ollama na GPU
potwierdzić wykorzystanie obu kart RTX 3080
zintegrować Ollama z Tracecat przez REST API

Najlepszym modelem dla konfiguracji 2× RTX 3080 10 GB okazał się Qwen3 14B, który działa w 100% na GPU i zapewnia bardzo dobrą wydajność inferencji.
