# linux-drill

Terminal-Quiz für Linux/Unix-Administration — deterministisch, seedbar, endlos spambar.

Gebaut als Interview- und RHCSA-Vorbereitung. Eine Frage ist eine **pure Funktion ihrer Nummer**: `random.seed(N)` ist die einzige Entropiequelle. Gleicher Seed = exakt dieselbe Frage, auf jeder Maschine, für immer. Falsch beantwortete Seeds sind dein Wiederholungs-Stapel.

> Fragen und Erklärungen sind derzeit auf **Deutsch** (entstanden für deutschsprachige Vorstellungsgespräche und EX200-Vorbereitung).

## Schnellstart

```bash
python3 quiz.py --run 20                 # Session: 20 Fragen, Score + Themenbilanz
python3 quiz.py --run 15 --topic selinux # nur ein Thema drillen
python3 quiz.py --exam                   # 25 Fragen quer durch alles
python3 quiz.py 137                      # Frage #137 — immer identisch
python3 quiz.py --seeds 42 881 17        # exakt diese Seeds (Repeat-Stapel)
python3 quiz.py --list                   # Themen + Umfang
```

Keine Abhängigkeiten außer Python 3. Keine Dateien, kein Zustand, kein Netzwerk.

## Was drin ist

- **141 handgeschriebene Fragen** über 14 Themen: Unix vs. Linux, Boot-Prozess, Prozesse & Signale, Dateisystem & Rechte, Performance, SSH & Benutzer, Patchmanagement (dnf/Satellite), SELinux, systemd, LVM, firewalld, TCP/IP-Grundlagen (DHCP, VLANs, ARP, Routing, NAT), Ansible, ITIL/Incident-Denken.
- **14 Generator-Archetypen** mit Parameter-Pools: Oktal-Rechte in beide Richtungen, Load-Average-Szenarien mit echten Zahlen, Befehls-Drills (dnf, SELinux, journalctl, firewalld, LVM, systemctl) in beide Richtungen, Standardports, Konfigurationspfade, Ansible-Module — und ein **Subnetting-Generator** (nutzbare Hosts, Masken, Netz-/Broadcast-Adressen), dessen CIDR-Mathematik testweise gegen Pythons `ipaddress`-Modul verifiziert ist.
- **712 distinkte Fragen**, gemessen über die Seeds 1–30000.
- Jede Antwort kommt mit Erklärung — das *Warum*, nicht nur das *Was*.
- Jede Session endet mit dem fertigen Replay-Kommando für alles, was falsch war.

## Design-Prinzipien

- Kein versteckter Zufall. Frage, Parameter und Antwort-Reihenfolge kommen aus einem `random.Random(seed)` — deterministisch replaybar.
- Fragen sind Daten, nicht Code: ein Tupel an `STATIC` anhängen genügt.
  ```python
  ("topic", "Frage?", ["RICHTIG", "falsch", "falsch", "falsch"], "Erklärung."),
  ```
  Die erste Option ist immer die richtige; gemischt wird zur Laufzeit.
- Generatoren sind pure Funktionen `rng -> Frage` — neue Drill-Familien in ~15 Zeilen.

## Roadmap

- [x] Netzwerk-Grundlagen-Pack (TCP/IP, DHCP, VLANs) + Subnetting-Generator
- [ ] Themen-Packs als eigene Datenmodule (Git, Docker/Podman, Kubernetes, Bash)
- [ ] Englische Fragenbank

Beiträge willkommen — eine gute Frage prüft das Verständnis, nicht das Auswendiggelernte, und die Distraktoren sind plausibel.

## Lizenz

MIT
