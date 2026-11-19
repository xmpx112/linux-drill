#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quiz.py — Interview-Quiz Linux/Unix (Deutsch), im Geist von mission.py.

Eine Frage ist eine pure Funktion ihrer Nummer: random.seed(N) ist die
einzige Entropiequelle. Gleiche Nummer = exakt gleiche Frage, für immer.
Falsch beantwortete Seeds sind dein Wiederholungs-Stapel.

Usage:
    python3 quiz.py                  # eine zufällige Frage (zeigt ihren Seed)
    python3 quiz.py 137              # Frage #137 (immer identisch)
    python3 quiz.py --run 20         # Session: 20 Fragen, Score + Themenbilanz
    python3 quiz.py --run 15 --topic selinux   # Session nur zu einem Thema
    python3 quiz.py --topic boot     # eine Zufallsfrage aus einem Thema
    python3 quiz.py --exam           # 25 Fragen quer durch alles
    python3 quiz.py --list           # Themen + Fragenzahl
    python3 quiz.py --seeds 42 17 93 # exakt diese Seeds nacheinander (Repeat-Stapel)

Design notes:
    - Kein versteckter Zufall. random.Random(N) erzeugt Frage, Parameter
      UND die Antwort-Reihenfolge — deterministisch replaybar.
    - Statische Bank + Generator-Archetypen mit Parameter-Pools; der
      kombinierte Fragenraum liegt deutlich über 300 distinkten Fragen.
    - Neue Fragen: einfach Tupel an STATIC anhängen (topic, frage,
      [richtig, falsch1, falsch2, falsch3], erklärung). Erste Option ist
      IMMER die richtige; gemischt wird zur Laufzeit.
"""

import ipaddress
import random
import sys

# ---------------------------------------------------------------------------
# Statische Fragenbank. Format:
#   (topic, frage, [RICHTIG, falsch, falsch, falsch], erklärung)
# ---------------------------------------------------------------------------

STATIC = [
    # ---------------- unix (G1) ----------------
    ("unix", "Was ist der Kernunterschied zwischen Unix und Linux?",
     ["Linux ist eine unabhängige, freie Neuimplementierung der Unix-Ideen; Unix ist eine Familie proprietärer Systeme gemeinsamer Abstammung",
      "Linux ist der Nachfolger von Unix und enthält dessen Quellcode",
      "Unix ist der Kernel, Linux das Userland darum herum",
      "Es gibt keinen — Linux ist ein zertifiziertes Unix"],
     "Torvalds schrieb 1991 einen neuen, freien Kernel NACH dem Vorbild von Unix — kein AT&T-Code. Gemeinsame Sprache ist POSIX."),
    ("unix", "Welcher Standard sorgt dafür, dass sich AIX, Solaris und Linux auf der Shell ähnlich anfühlen?",
     ["POSIX", "ANSI C", "LSB (Linux Standard Base)", "ISO 27001"],
     "POSIX normiert Shell-Verhalten, Systemaufrufe und Werkzeuge über die Unix-artige Welt hinweg."),
    ("unix", "Womit verwaltet man Dienste unter Solaris?",
     ["SMF — svcs / svcadm", "systemd — systemctl", "SRC — lssrc / startsrc", "OpenRC"],
     "Solaris: SMF (svcs, svcadm enable). SRC ist AIX. systemd ist Linux."),
    ("unix", "Welches Dateisystem ist unter Solaris nativ und vereint Volume-Management und Filesystem?",
     ["ZFS", "XFS", "JFS2", "ext4"],
     "ZFS: Pools, Snapshots, Checksummen integriert — kein separates LVM nötig. JFS2 ist AIX."),
    ("unix", "Paketinstallation unter modernem Solaris 11?",
     ["pkg install (IPS)", "dnf install", "installp", "apt-get install"],
     "Solaris 11 nutzt IPS (pkg). installp ist AIX, dnf ist RHEL."),
    ("unix", "Warum betreiben Konzerne wie Airbus noch echtes Unix (AIX/Solaris)?",
     ["Geschäftskritische Altanwendungen leben so lange wie ihre Missionen — Migration ist teuer und riskant",
      "Unix ist moderner und sicherer als Linux",
      "Linux ist für Serverbetrieb nicht zertifiziert",
      "Lizenzkosten von Linux sind höher"],
     "Legacy-Systeme (z. B. Satelliten-Bodensegmente auf Solaris/SPARC) werden gepflegt, nicht neu gebaut — daher 'heterogene Systemlandschaft'."),
    ("unix", "Was ist der Zusammenhang zwischen Fedora, RHEL und CentOS Stream?",
     ["Fedora ist Upstream-Innovation, CentOS Stream die Vorstufe, RHEL das stabilisierte Enterprise-Produkt",
      "RHEL ist die Testversion von Fedora",
      "CentOS Stream ist der kommerzielle Nachfolger von RHEL",
      "Fedora ist das LTS-Release von RHEL"],
     "Fedora → CentOS Stream → RHEL: vom Experimentierfeld zur Enterprise-Distribution mit Langzeit-Support."),
    ("unix", "Ein AIX-Admin sucht das Pendant zu journalctl/dmesg für Fehlerberichte. Was nennt er?",
     ["errpt", "svcs -xv", "syslogd -r", "aixlog"],
     "errpt ist der klassische AIX-Error-Report. Solches Vokabular zeigt konzeptionelle Unix-Vertrautheit."),

    # ---------------- boot (G2) ----------------
    ("boot", "In welcher Reihenfolge läuft ein moderner RHEL-Boot ab?",
     ["UEFI → GRUB2 → Kernel + initramfs → systemd → Default-Target",
      "GRUB2 → UEFI → systemd → Kernel → Targets",
      "UEFI → Kernel → GRUB2 → initramfs → systemd",
      "BIOS → systemd → GRUB2 → Kernel → Login"],
     "Firmware findet den Bootloader, GRUB lädt Kernel+initramfs, der Kernel startet systemd als PID 1, systemd fährt das Default-Target hoch."),
    ("boot", "Warum darf man /boot/grub2/grub.cfg nicht von Hand editieren?",
     ["Die Datei wird generiert — das nächste Kernel-Update überschreibt Handarbeit; Änderungen gehören nach /etc/default/grub bzw. grubby",
      "Die Datei ist kryptografisch signiert und wird sonst ungültig",
      "GRUB liest sie nur einmal bei der Installation",
      "Sie ist ein Symlink auf eine schreibgeschützte Datei"],
     "grub2-mkconfig bzw. grubby regenerieren grub.cfg; die Quelle der Wahrheit ist /etc/default/grub."),
    ("boot", "Wo liegt der Bootloader bei UEFI-Systemen?",
     ["Als Datei auf der EFI System Partition (FAT), gemountet unter /boot/efi",
      "Im ersten Sektor der Platte (MBR)",
      "In der initramfs",
      "Im NVRAM des Mainboards als Binärblob"],
     "UEFI versteht Dateisysteme und lädt den Bootloader als Datei von der ESP; Boot-Einträge verwaltet efibootmgr."),
    ("boot", "Was schützt Secure Boot?",
     ["Die Firmware startet nur signierte Bootloader — Schutz gegen Bootkits",
      "Die Festplattenverschlüsselung vor dem Login",
      "Das BIOS-Passwort vor Reset",
      "SSH-Logins während des Boots"],
     "Signaturprüfung in der Boot-Kette; in Defence-Umgebungen praktisch Pflicht."),
    ("boot", "Nach einem Storage-Umbau bootet der Server nicht mehr bis zum Root-FS. Welcher Befehl baut die initramfs neu?",
     ["dracut -f", "grub2-mkconfig -o /boot/grub2/grub.cfg", "mkinitcpio -p linux", "systemctl daemon-reload"],
     "dracut baut die initramfs pro Kernel; fehlen neue Storage-/LVM-Module, scheitert das Mounten des echten Root."),
    ("boot", "Mit welchem Kernel-Parameter hältst du den Boot in der initramfs an (z. B. für Root-Passwort-Reset)?",
     ["rd.break", "single", "init=/bin/false", "rescue=1"],
     "rd.break stoppt vor dem switch root: mount -o remount,rw /sysroot → chroot → passwd → touch /.autorelabel."),
    ("boot", "Warum gehört nach dem Root-Passwort-Reset via rd.break ein 'touch /.autorelabel' dazu?",
     ["/etc/shadow wurde außerhalb von SELinux geändert — ohne Relabel verweigert SELinux nach dem Boot Logins",
      "Damit GRUB den neuen Kernel erkennt",
      "Damit systemd die fstab neu einliest",
      "Damit das Passwort gehasht wird"],
     "Der Dateikontext stimmt nach dem Eingriff nicht mehr; autorelabel setzt beim nächsten Boot alle Kontexte neu — hier treffen sich Boot- und SELinux-Wissen."),
    ("boot", "Schwarzer Bildschirm, nicht einmal ein GRUB-Menü. Wo suchst du zuerst?",
     ["Firmware/Bootloader/Platte: Boot-Reihenfolge, wird die Disk erkannt, GRUB reparieren",
      "In journalctl -b nach Fehlern",
      "Im rescue.target die fstab prüfen",
      "Einen älteren Kernel booten"],
     "Kein GRUB = Stufe 1/2 der Kette. journalctl und Targets existieren erst, wenn der Kernel läuft — die Fehlersignatur nennt die Stufe."),

    # ---------------- prozesse (G3) ----------------
    ("prozesse", "Wie entstehen neue Prozesse unter Unix/Linux?",
     ["fork (Elternprozess kopiert sich) + exec (Kopie ersetzt sich durch das neue Programm)",
      "spawn: der Kernel erzeugt sie direkt aus der Binärdatei",
      "systemd erzeugt jeden Prozess im System",
      "clone der Binärdatei in den RAM durch die Shell"],
     "Das fork/exec-Modell erklärt den Prozessbaum: jeder Prozess hat eine PPID, ganz oben PID 1."),
    ("prozesse", "Was passiert mit Kindprozessen, deren Eltern sterben?",
     ["systemd (PID 1) adoptiert sie", "Sie werden sofort beendet", "Sie werden zu Zombies", "Der Kernel friert sie ein"],
     "Waisen werden an PID 1 umgehängt — deshalb räumt ein Neustart des fehlerhaften Parents auch Zombies ab."),
    ("prozesse", "Welches Signal sendet 'systemctl stop' zuerst an einen Dienst?",
     ["SIGTERM (15)", "SIGKILL (9)", "SIGHUP (1)", "SIGSTOP (19)"],
     "Erst die höfliche Bitte mit Aufräum-Chance; SIGKILL folgt nur nach Timeout."),
    ("prozesse", "Wofür steht SIGHUP bei Daemons konventionell?",
     ["Konfiguration neu einlesen ohne Neustart", "Sofort beenden", "Prozess pausieren", "Priorität erhöhen"],
     "Viele Dienste re-readen ihre Config bei HUP — moderner meist via systemctl reload."),
    ("prozesse", "Ein Prozess steht in ps dauerhaft auf Status 'D'. Was heißt das?",
     ["Uninterruptible sleep: er wartet auf I/O (Storage/NFS) und ignoriert selbst SIGKILL, bis das I/O zurückkommt",
      "Er ist ein Zombie und kann entfernt werden",
      "Er ist deaktiviert und startet beim nächsten Boot",
      "Er läuft mit niedrigster Priorität"],
     "D-State = das eigentliche Problem ist der Storage, kein Signal hilft. Praktiker-Wissen, das Interviewer hören wollen."),
    ("prozesse", "Wie senkst du die CPU-Priorität eines laufenden Prozesses?",
     ["renice +10 -p <PID>", "nice --kill <PID>", "chmod 400 /proc/<PID>", "systemctl slow <PID>"],
     "Höherer Nice-Wert = rücksichtsvoller. nice startet neu mit Priorität, renice ändert laufende Prozesse."),
    ("prozesse", "Viele Zombie-Prozesse sammeln sich an. Die richtige Maßnahme?",
     ["Den Elternprozess fixen oder neu starten — Zombies selbst sind schon tot und nicht killbar",
      "kill -9 auf alle Zombie-PIDs",
      "Den Server sofort rebooten",
      "swapoff/swapon, um die Prozesstabelle zu leeren"],
     "Ein Zombie ist nur ein nicht abgeholter Exit-Status in der Prozesstabelle; das Symptom sitzt beim Parent."),
    ("prozesse", "Womit findest und beendest du alle Prozesse, deren Kommandozeile 'backup' enthält?",
     ["pkill -f backup", "kill backup", "ps aux | kill", "killall -9 *backup*"],
     "pkill -f matched die volle Kommandozeile; erst ohne -9 (TERM), -9 nur als letzter Weg."),

    # ---------------- dateisystem (G4) ----------------
    ("dateisystem", "Was ist ein Inode?",
     ["Die Metadaten einer Datei (Besitzer, Rechte, Zeiger auf Datenblöcke) — ohne Namen; Namen wohnen in Verzeichnissen",
      "Der Dateiname samt Pfad",
      "Ein Cache-Eintrag des Kernels für offene Dateien",
      "Die Prüfsumme des Dateiinhalts"],
     "Ein Verzeichnis ist nur eine Tabelle Name→Inode. Daraus folgt die gesamte Link-Logik."),
    ("dateisystem", "Hardlink vs. Symlink — der korrekte Merksatz?",
     ["Hardlink = zweiter Name für denselben Inode; Symlink = eigene Datei, die einen Pfad enthält",
      "Hardlink = Kopie der Datei; Symlink = Verweis auf den Inode",
      "Beide sind identisch, Symlinks sind nur älter",
      "Hardlinks funktionieren nur auf Verzeichnissen"],
     "Deshalb: Hardlinks nur im selben FS und nicht auf Verzeichnisse; Symlinks können dangling sein."),
    ("dateisystem", "df meldet die Platte voll, du findet die Daten nicht. Klassische Ursache?",
     ["Eine gelöschte, aber noch von einem Prozess offen gehaltene Datei (z. B. Log) — lsof +L1, Prozess neu starten",
      "Das Dateisystem ist fragmentiert",
      "du zählt Hardlinks doppelt",
      "Der Inode-Cache ist voll"],
     "Gelöscht heißt: letzter NAME weg — die Datenblöcke leben, solange ein Prozess die Datei offen hält."),
    ("dateisystem", "Was bewirkt das x-Recht auf einem VERZEICHNIS?",
     ["Betreten/durchqueren — ohne x kommst du nicht an die Dateien darin, selbst wenn du ihre Namen kennst",
      "Dateien darin ausführen",
      "Das Verzeichnis löschen",
      "Rekursives Auflisten"],
     "r = Einträge auflisten, w = anlegen/löschen, x = betreten. Verzeichnisrechte ≠ Dateirechte — beliebte Fangfrage."),
    ("dateisystem", "Warum trägt /tmp die Rechte 1777?",
     ["Alle dürfen schreiben, aber das Sticky Bit erlaubt Löschen nur dem Datei-Besitzer",
      "Nur root darf schreiben, alle dürfen lesen",
      "Das SetUID-Bit beschleunigt temporäre Dateien",
      "1777 markiert tmpfs-Dateisysteme"],
     "Ohne Sticky Bit könnte in einem world-writable Verzeichnis jeder jedem alles weglöschen."),
    ("dateisystem", "Wozu dient das SetUID-Bit, z. B. auf /usr/bin/passwd?",
     ["Das Programm läuft mit den Rechten des Datei-Besitzers (root), damit User kontrolliert /etc/shadow ändern können",
      "Das Programm startet automatisch beim Boot",
      "Nur der Besitzer darf es ausführen",
      "Es markiert auditpflichtige Programme"],
     "find / -perm -4000 listet SetUID-Binaries — unerwartete Einträge sind ein Audit-Fund."),
    ("dateisystem", "Was bewirkt SetGID auf einem Verzeichnis?",
     ["Neue Dateien erben die Gruppe des Verzeichnisses statt der des Erstellers — der Mechanismus für Team-Shares",
      "Nur die Gruppe darf das Verzeichnis löschen",
      "Prozesse darin laufen mit Gruppenrechten",
      "Es verhindert Hardlinks"],
     "chmod g+s /srv/team sorgt für konsistente Gruppenzugehörigkeit in gemeinsamen Ablagen."),
    ("dateisystem", "Was sind /proc und /sys wirklich?",
     ["Fenster in den Kernel: virtuelle Dateisysteme, die Kernel-Datenstrukturen als Dateien zeigen",
      "Backup-Verzeichnisse des Systems",
      "RAM-Disks für temporäre Daten",
      "Mountpoints für Wechseldatenträger"],
     "'Alles ist eine Datei': cat /proc/cpuinfo liest Kernelzustand — deshalb funktionieren grep & Co. überall."),

    # ---------------- performance (G5) ----------------
    ("performance", "free -h: Welche Spalte zeigt, wie viel Speicher Anwendungen wirklich sofort bekommen könnten?",
     ["available", "free", "used", "shared"],
     "buff/cache ist verdrängbar; 'free' allein ist irreführend klein. available ist die ehrliche Zahl."),
    ("performance", "Wann ist Swap-Nutzung ein echtes Problem?",
     ["Bei ständigem Swap-VERKEHR (vmstat: si/so dauerhaft > 0) — nicht bei bloßem Swap-Bestand",
      "Sobald irgendetwas im Swap liegt",
      "Wenn Swap größer als RAM ist",
      "Swap ist auf Servern immer ein Problem"],
     "Geparkte inaktive Seiten sind gesund; permanentes Ein-/Auslagern heißt: RAM fehlt wirklich."),
    ("performance", "Der OOM-Killer hat zugeschlagen. Wo findest du den Beweis?",
     ["journalctl -k bzw. dmesg: 'Out of memory: Killed process ...'",
      "In /var/log/oom.log",
      "In der Ausgabe von free -h",
      "In ~/.bash_history des Dienstes"],
     "Ein Dienst, der 'einfach weg' war, ist ein OOM-Verdachtsfall — das unaufgefordert zu prüfen wirkt stark."),
    ("performance", "top zeigt hohen Wert bei %wa. Was bedeutet das?",
     ["CPU wartet auf I/O — der Engpass ist fast immer Disk oder NFS, nicht die CPU",
      "Viele Webanfragen (web access)",
      "Hohe Last durch Kernel-Threads",
      "Speicher wird aktiv ausgelagert"],
     "iowait ist der Verräter: Prozesse wollen arbeiten, der Storage liefert nicht. Weiter mit iostat -x 1."),
    ("performance", "Deine Diagnose-Reihenfolge bei 'Server ist langsam'?",
     ["uptime → top (CPU vs. RAM vs. %wa) → free/vmstat → iostat → journalctl -p err — feste Reihenfolge statt Bauchgefühl",
      "Sofort rebooten, dann Logs lesen",
      "Erst iostat, dann uptime, dann Dienste neu starten",
      "Alle Dienste einzeln neu starten, bis es schneller wird"],
     "Die feste Reihenfolge ist dein Autopilot unter Stress — und genau das prüft die Frage im Interview."),
    ("performance", "Die Load-Werte sind 1min=12, 5min=6, 15min=2. Interpretation?",
     ["Die Last steigt gerade stark an — das Problem ist akut und frisch",
      "Die Last klingt ab, das Problem ist vorbei",
      "Die Werte sind fehlerhaft",
      "Das System ist im Leerlauf"],
     "1-min über 15-min = Verschlechterung im Gange. Umgekehrt wäre es am Abklingen."),
    ("performance", "Warum zählt Linux I/O-wartende Prozesse in den Load Average ein?",
     ["Load misst laufWILLIGE Prozesse — auch wer auf Disk wartet, will arbeiten; so zeigt Load Engpässe jenseits der CPU",
      "Ein Implementierungsfehler, der aus Kompatibilität bleibt",
      "Damit der Wert größer aussieht",
      "Nur Solaris macht das, Linux nicht"],
     "Deshalb: hoher Load + niedrige CPU = I/O-Problem. Schnellere CPUs würden nichts helfen."),

    # ---------------- ssh_user (G6) ----------------
    ("ssh_user", "Warum liegen Passwort-Hashes in /etc/shadow statt in /etc/passwd?",
     ["passwd muss weltlesbar sein (UID→Name-Auflösung); die Geheimnisse wandern in eine nur für root lesbare Datei",
      "shadow ist verschlüsselt, passwd nicht",
      "Aus historischen Gründen ohne Sicherheitsnutzen",
      "passwd ist zu klein für Hashes"],
     "Trennung von öffentlichen Metadaten und Geheimnissen mit getrennten Rechten — das Lehrstück dahinter."),
    ("ssh_user", "Was ist der klassische Unfall bei 'usermod -G gruppe user'?",
     ["Ohne -a ERSETZT -G alle bisherigen Gruppen des Users statt zu ergänzen",
      "Der User wird gesperrt",
      "Die Gruppe wird gelöscht und neu angelegt",
      "Das Home-Verzeichnis wechselt den Besitzer"],
     "usermod -aG gruppe user — das -a (append) nicht vergessen."),
    ("ssh_user", "Warum editiert man sudoers mit visudo statt direkt?",
     ["visudo prüft die Syntax vor dem Speichern — eine kaputte sudoers sperrt sonst alle von sudo aus",
      "Nur visudo kann die Datei entschlüsseln",
      "Direktes Editieren ist von SELinux verboten",
      "visudo erstellt automatisch Backups im Git"],
     "Gleiches Muster wie mount -a nach fstab-Änderung: Fehler finden, solange man noch handlungsfähig ist."),
    ("ssh_user", "Warum ist Key-Authentifizierung sicherer als Passwörter bei SSH?",
     ["Der private Schlüssel verlässt nie den Client; übertragen wird nur ein Signatur-Beweis — kein Geheimnis unterwegs, Brute-Force sinnlos",
      "Keys sind länger und daher schwerer zu tippen",
      "Keys werden stündlich rotiert",
      "SSH verschlüsselt Passwörter nicht"],
     "Asymmetrische Kryptografie: Besitz-Beweis statt Geheimnis-Übertragung. Pro Gerät ein Key = sauber entziehbar."),
    ("ssh_user", "Warum PermitRootLogin no — auch mit Keys?",
     ["Personalisierte Logins + sudo machen nachvollziehbar, WER was getan hat — entscheidend für Audits",
      "Root-Keys sind technisch unsicherer",
      "SSH unterstützt root nicht mehr",
      "Damit Fail2ban funktioniert"],
     "Ein geteilter root-Zugang zerstört die Zurechenbarkeit. In Compliance-Umgebungen ein Kernargument."),
    ("ssh_user", "Die Profi-Gewohnheit nach jeder sshd_config-Änderung?",
     ["reload bei OFFENER Session und einen NEUEN Test-Login machen, bevor man sich abmeldet",
      "Sofort rebooten",
      "Die alte Session schließen und neu verbinden",
      "sshd stoppen, Datei ändern, sshd starten"],
     "Die offene Session ist die Lebensversicherung gegen Selbst-Aussperrung."),
    ("ssh_user", "Was bewirkt '2>&1' am Ende eines Befehls?",
     ["stderr wird dorthin umgeleitet, wo stdout gerade hingeht — Fehler und Ausgabe landen zusammen",
      "Der Befehl läuft mit doppelter Priorität",
      "stdout wird verworfen, stderr bleibt",
      "Der Befehl wird zweimal ausgeführt"],
     "Klassiker: befehl > log 2>&1 — alles in eine Datei. Reihenfolge der Umleitungen zählt."),
    ("ssh_user", "Warum sind systemd-Timer auf RHEL Cron meist vorzuziehen?",
     ["Logs im Journal, Persistent=true holt verpasste Läufe nach, Abhängigkeiten auf andere Units, list-timers als Übersicht",
      "Cron ist auf RHEL nicht mehr installierbar",
      "Timer laufen mit höherer Priorität",
      "Cron kann keine Minuten-Auflösung"],
     "Ein verpasster Cron-Lauf nach Reboot ist einfach weg; ein Timer mit Persistent=true nicht. Zeigt, dass du nicht 2015 stehengeblieben bist."),

    # ---------------- patch (K1) ----------------
    ("patch", "Nur sicherheitsrelevante Updates einspielen — der Befehl?",
     ["dnf upgrade --security", "dnf update --all --cve", "dnf install security", "dnf patch --sec"],
     "Vorher sichten: dnf updateinfo list security. Minimale Änderung = minimales Risiko in Prod."),
    ("patch", "Wie machst du eine fehlgeschlagene dnf-Transaktion rückgängig?",
     ["dnf history, dann dnf history undo <ID>", "dnf rollback --last", "rpm --undo", "dnf erase --transaction"],
     "Jede Transaktion ist protokolliert. Grenze: bei Kernel/tiefen Libraries ist der sauberere Rollback der Boot in den alten Kernel."),
    ("patch", "Woran erkennst du nach dem Patchen, ob ein Reboot nötig ist?",
     ["needs-restarting -r (Exit-Code)", "dnf check-reboot", "uptime", "systemctl is-rebooting"],
     "Kernel/glibc betroffen → Reboot; sonst laufen alte Versionen im Speicher weiter."),
    ("patch", "Warum patcht man zuerst in der Staging-/Testumgebung?",
     ["Ob ein Update kompatibel ist, kann man nicht wissen, nur beobachten — also soll es seinen ersten Fehler machen, wo es nicht wehtut",
      "Weil Prod-Repos langsamer sind",
      "Weil dnf in Prod keine Updates erlaubt",
      "Weil Staging die Lizenzprüfung übernimmt"],
     "Risikologik, nicht Formalismus: Beobachtung ersetzt Hoffnung."),
    ("patch", "Wozu dienen Content Views in Red Hat Satellite?",
     ["Eingefrorene Repo-Stände, die durch Lifecycle-Umgebungen (Dev→Test→Prod) wandern — Prod bekommt exakt den getesteten Paketstand",
      "Dashboards für Patch-Statistiken",
      "Container-Images für Deployments",
      "Benutzerrollen für die Satellite-GUI"],
     "Der Kerngedanke zentraler Patch-Orchestrierung: identische, geprüfte Versionen statt 'was heute im Internet-Repo liegt'."),
    ("patch", "Warum bleibt nach einem Kernel-Update der alte Kernel installiert?",
     ["Als Rollback: Bei Problemen bootet man im GRUB-Menü einfach die vorherige Version",
      "dnf kann Kernel nicht löschen",
      "Für die Lizenzprüfung von Red Hat",
      "Damit initramfs-Backups existieren"],
     "RHEL behält standardmäßig mehrere Kernel — genau dafür existiert das GRUB-Menü."),
    ("patch", "Der wichtigste Schritt NACH dem Einspielen eines Patches im Wartungsfenster?",
     ["Aktive Verifikation im Monitoring: Dienste oben, Fehlerraten normal — 'keine Fehlermeldung' ist kein Beweis",
      "Sofort das nächste System patchen",
      "Den Patch dokumentieren und Feierabend machen",
      "Alle Dienste vorsorglich neu starten"],
     "Der Satz, der bei einem Ops-Chef punktet: Verifikation gehört zum Change, nicht zum Zufall."),
    ("patch", "Womit registriert man ein RHEL-System für Updates bei Red Hat?",
     ["subscription-manager register", "dnf login", "rhn-connect", "satellite-join"],
     "Ohne Subscription keine Repos. In Konzernen übernimmt das meist Satellite/Activation Keys."),

    # ---------------- selinux (K2) ----------------
    ("selinux", "DAC vs. MAC — was ergänzt SELinux?",
     ["Eine zentrale, verpflichtende Kernel-Policy (MAC) ZUSÄTZLICH zu den Besitzer-verwalteten Dateirechten (DAC) — beides muss erlauben",
      "Es ersetzt die klassischen Dateirechte komplett",
      "Eine Benutzerverwaltung mit Rollen statt Gruppen",
      "Eine Firewall auf Dateisystem-Ebene"],
     "Default Deny per Policy: Der gekaperte Webserver darf /etc/shadow auch dann nicht lesen, wenn rwx es erlauben würde."),
    ("selinux", "Welcher Teil eines SELinux-Kontexts entscheidet in der Praxis (Type Enforcement)?",
     ["Der Typ, endet auf _t (z. B. httpd_sys_content_t)", "Der SELinux-User (system_u)", "Die Rolle (object_r)", "Das Level (s0)"],
     "Die Policy ist eine Regelliste über Typen: Prozess-Typ X darf auf Datei-Typ Y. ls -Z zeigt Kontexte."),
    ("selinux", "Warum ist 'setenforce 0' zur Diagnose legitim, 'disabled' in der Config aber nicht?",
     ["Permissive protokolliert weiter und gilt nur bis zum Reboot; disabled wirft den Schutz weg und erzwingt beim Reaktivieren ein komplettes Relabel",
      "setenforce 0 wirkt nur auf einzelne Prozesse",
      "disabled ist identisch, nur dauerhaft — beides ist gleich okay",
      "Permissive blockiert weiterhin kritische Zugriffe"],
     "Diagnose-Modus mit Rückweg vs. Abschalten mit Folgekosten. In Compliance-Umgebungen ist disabled keine Option."),
    ("selinux", "Ein eigener Webroot /srv/web soll DAUERHAFT den richtigen Kontext bekommen. Der saubere Weg?",
     ["semanage fcontext -a -t httpd_sys_content_t '/srv/web(/.*)?' und dann restorecon -R /srv/web",
      "chcon -R -t httpd_sys_content_t /srv/web — fertig",
      "setenforce 0 für dieses Verzeichnis",
      "Die Dateien nach /var/www kopieren und zurücklinken"],
     "chcon allein überlebt kein Relabel; semanage trägt die Erwartung in die Policy ein, restorecon wendet sie an."),
    ("selinux", "Apache soll ausgehende Netzverbindungen öffnen dürfen (Proxy). Erste Anlaufstelle?",
     ["Ein Boolean: setsebool -P httpd_can_network_connect on",
      "Ein eigenes Policy-Modul schreiben",
      "audit2allow über alle Denials laufen lassen",
      "SELinux auf permissive stellen"],
     "Red Hat hat häufige Sonderfälle als Schalter vorgedacht — getsebool -a | grep httpd zuerst prüfen."),
    ("selinux", "Ein Dienst soll auf Port 8081 lauschen, SELinux blockiert. Der richtige Befehl?",
     ["semanage port -a -t http_port_t -p tcp 8081", "firewall-cmd --add-port=8081/tcp", "setsebool -P port_8081 on", "chcon -p 8081 httpd"],
     "Auch Ports tragen Typen. firewalld ist die andere, unabhängige Schicht — beide müssen passen."),
    ("selinux", "Wo und wie liest du SELinux-Denials?",
     ["ausearch -m AVC -ts recent (aus /var/log/audit/audit.log)", "journalctl -u selinux", "cat /var/log/selinux/denied.log", "dmesg | grep DENIED"],
     "Der Denial nennt Prozess-Typ und Datei-Typ — damit weißt du exakt, was zu fixen ist (Kontext oder Boolean)."),
    ("selinux", "Der Interview-Satz, der bei SELinux-Fragen NIE fallen darf?",
     ["'Ich schalte SELinux aus' — richtig ist: diagnostizieren (ausearch), gezielt fixen (restorecon/semanage/Boolean), enforcing bestätigen",
      "'Ich prüfe erst getenforce'",
      "'Ich stelle temporär auf permissive'",
      "'Ich suche zuerst nach einem Boolean'"],
     "Abschalten = Schutzweste ausziehen, weil sie zwickt. Die Denkweise ist das eigentliche Prüfkriterium."),

    # ---------------- systemd (K3) ----------------
    ("systemd", "Eigene Anpassung an einer Paket-Unit, die Updates überlebt?",
     ["systemctl edit <dienst> — Override-Snippet unter /etc/systemd/system, /etc gewinnt immer über /usr/lib",
      "Die Unit in /usr/lib/systemd/system direkt editieren",
      "Die Unit kopieren und das Original löschen",
      "Ein Shellskript in /etc/rc.local"],
     "Paket-Updates überschreiben nur /usr/lib. Nach Änderungen: systemctl daemon-reload — systemd cached Unit-Dateien."),
    ("systemd", "Warum braucht es nach dem Ändern einer Unit-Datei 'systemctl daemon-reload'?",
     ["systemd hält Unit-Dateien im Speicher gecacht und arbeitet sonst mit dem alten Stand",
      "Damit der Dienst neu startet",
      "Um die Datei auf Syntaxfehler zu prüfen",
      "Um SELinux-Kontexte zu aktualisieren"],
     "Ohne reload jagst du ein Phantom: Datei neu, Verhalten alt."),
    ("systemd", "Unterschied 'systemctl enable' vs. 'systemctl start'?",
     ["enable = beim Boot starten (Symlink ins Target), start = jetzt starten; enable --now macht beides",
      "enable startet mit höherer Priorität",
      "start wirkt dauerhaft, enable nur bis zum Reboot",
      "Es gibt keinen Unterschied"],
     "Der Anfängerfehler: Dienst läuft, ist aber nach dem nächsten Reboot weg — oder umgekehrt."),
    ("systemd", "Logs des letzten Boots ansehen (der Server ist unerwartet neu gestartet)?",
     ["journalctl -b -1", "journalctl --reboot", "cat /var/log/lastboot", "dmesg --previous"],
     "-b = dieser Boot, -b -1 = der davor. Gold für die Frage 'warum ist er neu gestartet?'."),
    ("systemd", "Unterschied rescue.target vs. emergency.target?",
     ["rescue: Minimalsystem mit Root-Shell, Dateisysteme gemountet; emergency: noch minimaler, Root-FS read-only",
      "rescue ist für Netzwerkprobleme, emergency für Storage",
      "emergency hat GUI, rescue nicht",
      "Beide sind identisch, nur historisch doppelt benannt"],
     "Bei kaputter fstab landet systemd oft selbst im emergency.target — remount rw, fixen, mount -a."),
    ("systemd", "Der Boot hängt bei 'A start job is running for ...'. Häufigste Ursache?",
     ["Ein fstab-/Mount-Eintrag, der nicht verfügbar ist — systemd wartet auf das generierte mount-Unit-Timeout",
      "Ein Kernel-Panic",
      "GRUB findet die initramfs nicht",
      "SELinux relabelt das Dateisystem"],
     "Signatur der systemd-Stufe: rescue/emergency booten, journalctl -xb, fstab prüfen. Prävention: mount -a nach jeder Änderung."),
    ("systemd", "Dauerhaft ohne GUI booten — der Befehl?",
     ["systemctl set-default multi-user.target", "systemctl disable graphical", "runlevel 3", "grubby --no-gui"],
     "Targets sind der Runlevel-Nachfolger; get-default zeigt den Ist-Zustand."),
    ("systemd", "Nur die Fehler-Logs eines Dienstes seit einer Stunde?",
     ["journalctl -u <dienst> -p err --since \"1 hour ago\"", "journalctl --errors <dienst>", "grep ERROR /var/log/messages", "systemctl errors <dienst>"],
     "Ein Werkzeug, eine Zeitachse, filterbar — der Vorteil des Journals gegenüber Log-Dateien-Grepping."),

    # ---------------- lvm (K4) ----------------
    ("lvm", "Das Drei-Ebenen-Modell von LVM in der richtigen Reihenfolge?",
     ["PV (Platte/Partition) → VG (Pool aus PVs) → LV (flexible 'Partition' mit Dateisystem)",
      "LV → VG → PV",
      "VG → PV → LV",
      "PV → LV → VG"],
     "Zutat → Topf → Portion. Ab der VG ist egal, auf welcher physischen Platte etwas liegt."),
    ("lvm", "Warum IMMER lvextend mit -r (--resizefs)?",
     ["Ohne wächst nur der 'Behälter' — das Dateisystem bleibt klein und df zeigt weiter voll; -r vergrößert beides in einem Schritt",
      "-r aktiviert die Online-Vergrößerung, sonst braucht es unmount",
      "-r legt vorher einen Snapshot an",
      "Ohne -r gehen Daten verloren"],
     "Die klassische Falle: LV größer, df unverändert, verwirrte Fehlersuche."),
    ("lvm", "Die VG hat kein VFree mehr, /var braucht Platz. Reihenfolge?",
     ["Neue Platte → pvcreate → vgextend → lvextend -r — kein Service merkt etwas",
      "lvreduce auf einem anderen LV, dann lvextend",
      "Das LV löschen und größer neu anlegen",
      "resize2fs direkt auf der neuen Platte"],
     "Genau das ist der LVM-Gewinn: Platte rein, Pool wächst, live erweitern."),
    ("lvm", "XFS vs. ext4 — der eine Satz für RHEL?",
     ["XFS ist Standard und kann nur WACHSEN (xfs_growfs); ext4 kann offline auch schrumpfen",
      "ext4 ist Standard, XFS ist Legacy",
      "XFS kann online schrumpfen, ext4 nicht",
      "Beide können beliebig wachsen und schrumpfen"],
     "Design-Konsequenz: LVs knapp anlegen und wachsen lassen — verkleinern hieße bei XFS neu anlegen und umkopieren."),
    ("lvm", "Warum stehen in /etc/fstab UUIDs statt /dev/sdb1?",
     ["sdX-Namen können bei jedem Boot neu vergeben werden; die UUID klebt am Dateisystem und ist boot-stabil",
      "UUIDs mounten schneller",
      "sdX-Namen sind seit RHEL 9 abgeschafft",
      "UUIDs verschlüsseln den Eintrag"],
     "Eine zusätzliche Platte oder anderer Controller-Scan, und aus sdb wird sdc. blkid zeigt die UUIDs."),
    ("lvm", "Die Profi-Gewohnheit direkt nach jeder fstab-Änderung?",
     ["mount -a (bzw. findmnt --verify) — der Tippfehler fällt JETZT auf, nicht beim nächsten Boot im emergency.target",
      "Sofort rebooten zum Testen",
      "systemctl daemon-reload",
      "Die alte fstab löschen"],
     "Der Alternativ-Zeitpunkt des Fehlers ist nachts, beim Reboot, ohne dich."),
    ("lvm", "Platte 'voll' — aber erst Ursache, dann Kapazität. Welcher Befehl zeigt dir das WAS?",
     ["du -xh --max-depth=1 auf dem Mountpoint", "df -h", "lsblk", "vgs"],
     "df zeigt WO, du zeigt WAS — oft Logs, dann ist logrotate die Lösung, nicht mehr Platz."),
    ("lvm", "Wofür steht das -x bei 'du -x'?",
     ["Bleibe im selben Dateisystem — andere Mounts (z. B. /proc, NFS) werden nicht mitgezählt",
      "Zeige erweiterte Attribute",
      "Sortiere nach Größe",
      "Folge Symlinks"],
     "Ohne -x zählt du munter über Mountgrenzen und liefert irreführende Summen."),

    # ---------------- netz (K5) ----------------
    ("netz", "Das Zonen-Konzept von firewalld — wozu?",
     ["Jede Schnittstelle gehört zu einer Zone mit eigenem Vertrauensniveau — Policy pro Netzsegment statt flacher Regelliste",
      "Zonen trennen IPv4 und IPv6",
      "Zonen sind DNS-Bereiche für interne Namen",
      "Zonen gruppieren Benutzer nach Rechten"],
     "Dieselbe Denke wie VLAN-Segmentierung, nur auf Host-Ebene — der Satz, mit dem du es an deine OPNsense-Erfahrung anbindest."),
    ("netz", "Warum existiert bei firewalld die Trennung runtime vs. permanent?",
     ["Runtime testet gefahrlos (ein Reboot/Reload stellt alles zurück) — permanent wird eine Regel erst, wenn sie bewiesen funktioniert: Schutz vor Selbst-Aussperrung",
      "Permanent-Regeln sind performanter",
      "Runtime-Regeln gelten nur für root",
      "Ein historisches Relikt aus iptables-Zeiten"],
     "Der eingebaute Schutz vor 'Firewall-Änderung remote, Verbindung tot, Anfahrt ins RZ'."),
    ("netz", "Eine permanente Regel wurde angelegt, wirkt aber nicht. Was fehlt?",
     ["firewall-cmd --reload — permanent landet erst in der Config, aktiv wird es durch den Reload",
      "systemctl restart network",
      "Ein Reboot",
      "setsebool -P firewall_apply on"],
     "--permanent schreibt, --reload aktiviert (und verwirft runtime-only-Änderungen)."),
    ("netz", "Erster Befehl, um den Ist-Zustand der Host-Firewall zu sehen?",
     ["firewall-cmd --list-all", "iptables -S", "ss -tulpen", "nft show all"],
     "Zeigt aktive Zone, Services, Ports, Rich Rules — immer der erste Blick."),
    ("netz", "'Server erreicht Dienst X nicht' — deine Prüf-Reihenfolge?",
     ["dig (löst der Name?) → Resolver prüfen → ping (Host da?) → nc/curl auf den Port (Firewall?) → ip route",
      "Erst Routing, dann DNS, dann Port",
      "Sofort tcpdump auf allen Interfaces",
      "Dienst neu starten, dann testen"],
     "Vom Namen zur Leitung: Der häufigste Fehler sitzt vorn — 'Ist es DNS?' ist aus gutem Grund das Branchen-Running-Gag."),
    ("netz", "Wie unterscheidest du 'Host weg' von 'Firewall blockt Port'?",
     ["ping antwortet, aber nc -zv host port scheitert → Host lebt, der Port ist zu",
      "Beides sieht identisch aus",
      "traceroute zeigt den Unterschied in Hop 1",
      "dig liefert bei Firewall-Block SERVFAIL"],
     "Erreichbarkeit der IP und Erreichbarkeit des Ports sind zwei getrennte Fragen — genau so im Interview formulieren."),
    ("netz", "Womit konfiguriert RHEL Netzwerk-Interfaces?",
     ["NetworkManager — nmcli con show/mod/up", "ifconfig und /etc/network/interfaces", "netplan apply", "systemd-networkd ausschließlich"],
     "nmcli-Grundform kennen reicht für Runde 1; ifcfg-Dateien sind Legacy, netplan ist Ubuntu."),
    ("netz", "Welche Services gehören minimal in die Zone eines gehärteten Webservers?",
     ["Nur was die Rolle braucht: http/https (+ ssh aus dem Management-Netz) — Default Deny als Haltung",
      "Alle Standard-Services, um Support zu erleichtern",
      "Gar keine — die Perimeter-Firewall reicht",
      "dhcpv6-client und samba für Discovery"],
     "Host-Firewall ergänzt den Netzrand: Jede Schicht nach demselben Prinzip minimal."),

    # ---------------- ansible (K6) ----------------
    ("ansible", "Was heißt 'agentless' bei Ansible — und warum zählt das?",
     ["Auf Zielservern läuft nichts von Ansible: Push per SSH, drüben nur Python — nichts zu installieren, zu patchen, abzusichern",
      "Ansible braucht keinen Controller",
      "Es funktioniert ohne Netzwerkverbindung",
      "Die Playbooks laufen clientseitig im Browser"],
     "Bei hunderten Servern und in Security-Umgebungen ein riesiger Unterschied zu agentenbasierten Tools."),
    ("ansible", "Idempotenz in einem Satz?",
     ["Module prüfen den Ist-Zustand und tun nur, was zum Soll fehlt — derselbe Lauf ist beliebig oft wiederholbar, ohne Schaden",
      "Jede Task läuft exakt einmal pro Host",
      "Playbooks können nicht fehlschlagen",
      "Änderungen werden automatisch zurückgerollt"],
     "Deshalb korrigiert ein regelmäßig laufendes Playbook nebenbei Konfigurationsdrift — das leistet kein Shell-Skript."),
    ("ansible", "Wozu dient ein Handler?",
     ["Er läuft nur, wenn ihn eine Task per notify ausgelöst hat — und gesammelt am Ende: z. B. Reload nur bei tatsächlich geänderter Config",
      "Er behandelt Fehler und rollt zurück",
      "Er verteilt Tasks auf mehrere Hosts parallel",
      "Er verwaltet SSH-Verbindungen"],
     "Config unverändert → kein notify → kein Reload → der Dienst wird nie unnötig angefasst. Betriebsschonendes Denken."),
    ("ansible", "Was bedeutet 'state: present' beim dnf-Modul?",
     ["Deklarativ: 'Das Paket SOLL vorhanden sein' — ist es da, passiert nichts (ok); fehlt es, wird installiert (changed)",
      "Installiere das Paket bei jedem Lauf neu",
      "Prüfe nur, ohne zu installieren",
      "Halte das Paket auf der aktuellsten Version"],
     "Soll-Zustand statt Ablauf — DER Unterschied zur imperativen Skript-Welt. ('latest' wäre: aktuellste Version.)"),
    ("ansible", "Der eingebaute Trockenlauf vor einem Prod-Rollout?",
     ["ansible-playbook site.yml --check", "ansible-playbook site.yml --dry", "--simulate", "--test-only"],
     "Zeigt, was sich ändern WÜRDE, ändert nichts. Die Generalprobe gehört vor jeden Prod-Lauf."),
    ("ansible", "Wo gehören Secrets (Passwörter, Keys) in Ansible hin?",
     ["Ansible Vault — verschlüsselt im Repo, entschlüsselt zur Laufzeit",
      "In group_vars im Klartext, Zugriff regelt Git",
      "Als Umgebungsvariablen auf den Zielhosts",
      "In die Inventory-Datei"],
     "Klartext-Secrets im Repo sind ein Audit-Fund — Vault ist der vorgesehene Ort."),
    ("ansible", "Was ist eine Role?",
     ["Ein wiederverwendbarer Playbook-Baustein in Standard-Ordnerstruktur (tasks, handlers, templates, defaults)",
      "Ein Benutzerkonto auf dem Controller",
      "Eine Berechtigungsstufe im Inventory",
      "Ein Synonym für ein Play"],
     "Die 'nginx-Rolle' einmal bauen, überall einbinden — so skaliert Teamarbeit mit Ansible."),
    ("ansible", "Warum schlägt ein Playbook ein gleichwertiges Shell-Skript?",
     ["Zustände statt Abläufe: idempotent wiederholbar, Inventory statt ssh-Schleifen, --check als Generalprobe, YAML als lesbare Doku des Soll-Zustands",
      "Playbooks laufen grundsätzlich schneller",
      "Shell-Skripte funktionieren nicht über SSH",
      "YAML kann Schleifen, Bash nicht"],
     "Bash behält seinen Platz: Diagnosen, Einzeiler, Glue. Konfiguration gehört in deklarierte Zustände."),

    # ---------------- itil (K7) ----------------
    ("itil", "Incident vs. Problem — die Kurzdefinition?",
     ["Incident: Service schnellstmöglich wiederherstellen (notfalls Workaround); Problem: die Ursache dahinter finden und dauerhaft beseitigen",
      "Incident ist klein, Problem ist groß",
      "Incident meldet der User, Problem das Monitoring",
      "Problem ist die Eskalationsstufe eines Incidents"],
     "Zwei entgegengesetzte Modi: Geschwindigkeit während der Störung, Gründlichkeit danach."),
    ("itil", "Warum trennt ITIL Incident- und Problem-Management überhaupt?",
     ["Wer beides vermischt, macht beides schlecht: forscht während des Feuers oder löscht für immer nur Symptome",
      "Aus Abrechnungsgründen zwischen Abteilungen",
      "Weil Tickets sonst zu lang werden",
      "Historisch gewachsen, ohne sachlichen Grund"],
     "Während der Störung ist der Neustart legitim; danach wäre 'war ja nur ein Neustart nötig' fahrlässig."),
    ("itil", "Was ist ein Known Error?",
     ["Ein Problem mit bekannter Ursache und dokumentiertem Workaround — beim nächsten Mal Minuten statt Stunden",
      "Ein Fehler, den der Hersteller nicht fixen will",
      "Ein Incident, der dreimal auftrat",
      "Ein abgelehnter Change"],
     "Die Wissensdatenbank des Betriebs: dokumentierte Abkürzungen für wiederkehrende Störungen."),
    ("itil", "Wonach priorisierst du bei zwei gleichzeitigen Störungen?",
     ["Auswirkung × Dringlichkeit: wie viele betroffen, wie geschäftskritisch — nach Logik, nicht nach Lautstärke des Anrufers",
      "First come, first served",
      "Nach Seniorität des Melders",
      "Immer zuerst das technisch interessantere"],
     "Impact × Urgency ist das Standardraster — und die ehrliche Antwort auf 'wer zuerst?'."),
    ("itil", "Der meistübersehene Schritt während eines Incidents?",
     ["Früh und aktiv kommunizieren: was gestört ist, woran du arbeitest, wann das nächste Update — zwei Sätze kaufen Ruhe zum Arbeiten",
      "Ein Backup ziehen",
      "Den Incident sofort als Problem klassifizieren",
      "Die Zeitachse erst nach der Lösung schreiben"],
     "Ohne Status: zehn Rückfragen, unkoordinierte 'Hilfe', Management-Eskalation aus Blindflug. Ops-Chefs hören auf genau diesen Punkt."),
    ("itil", "Warum gehört die Post-Mortem-Analyse 'blamefrei' geführt?",
     ["Wer Schuldige sucht, bekommt beim nächsten Mal vertuschte Fehler statt früher Meldung",
      "Aus arbeitsrechtlichen Gründen",
      "Weil die Ursache nie bei Personen liegt",
      "Damit das Protokoll kürzer wird"],
     "Die Kultur-Frage hinter dem Prozess: Transparenz entsteht nur ohne Angst."),
    ("itil", "Was ist ein Change im ITIL-Sinn?",
     ["Eine geplante, genehmigte Änderung an Produktivsystemen — weil die meisten Incidents durch unkontrollierte Änderungen entstehen",
      "Jede beliebige Änderung an einem Server",
      "Der Wechsel eines Bearbeiters im Ticket",
      "Ein Software-Release des Herstellers"],
     "'Was wurde zuletzt geändert?' ist die erste Frage jeder Störungsanalyse — Change-Disziplin ist Incident-Prävention."),
    ("itil", "Der letzte Schritt nach gelöster Störung, der den Kreis schließt?",
     ["Einen Monitoring-Check für die Früherkennung ergänzen und den Fall dokumentieren",
      "Das Ticket kommentarlos schließen",
      "Den betroffenen Server vorsorglich neu installieren",
      "Eine Mail an alle Mitarbeitenden"],
     "Dauerhafte Maßnahme + Früherkennung + Doku = aus einem Incident wird Betriebsreife. Genau deine Monitoring-Denke."),

    # ---------------- Nachschlag: 2 pro Thema ----------------
    ("unix", "Auf welcher Hardware-Plattform laufen klassische Solaris-Systeme typischerweise?",
     ["SPARC", "x86 ausschließlich", "POWER", "ARM64"],
     "Solaris/SPARC ist das klassische Paar (AIX läuft auf POWER) — die Hardware-Bindung ist die halbe Migrations-Hürde."),
    ("unix", "Womit verwaltet AIX seine Dienste?",
     ["SRC — lssrc / startsrc / stopsrc", "systemd — systemctl", "SMF — svcadm", "init.d-Skripte ausschließlich"],
     "AIX: System Resource Controller. SMF ist Solaris, systemd ist Linux — gleiche Idee, drei Vokabulare."),
    ("boot", "Womit siehst und verwaltest du UEFI-Boot-Einträge im NVRAM?",
     ["efibootmgr", "grub2-mkconfig", "bootctl --mbr", "dracut --list-boot"],
     "efibootmgr -v zeigt die Einträge; UEFI führt Buchhaltung über bootfähige Dateien auf der ESP."),
    ("boot", "Kernel-Panic sofort nach GRUB, direkt nach einem Kernel-Update. Schnellste Abhilfe?",
     ["Im GRUB-Menü den vorherigen Kernel booten — RHEL behält ihn genau dafür",
      "Von einem Live-USB booten und den Kernel neu installieren",
      "rd.break setzen und die initramfs löschen",
      "Das BIOS auf Werkseinstellungen zurücksetzen"],
     "Die Fehlersignatur nennt die Stufe (Kernel), das GRUB-Menü ist der eingebaute Rollback — erst Betrieb wiederherstellen, dann Ursache klären."),
    ("prozesse", "Was zeigt die PPID-Spalte in ps -ef?",
     ["Die PID des Elternprozesses — so wird der Prozessbaum aus fork/exec sichtbar",
      "Die Priorität des Prozesses",
      "Die PID des zuletzt gestarteten Kindprozesses",
      "Die Prozessgruppe für Signale"],
     "Jeder Prozess hat einen Parent, ganz oben PID 1 (systemd). pstree zeigt denselben Baum grafisch."),
    ("prozesse", "Welche Dateien hält ein Prozess gerade offen?",
     ["lsof -p <PID>", "ps --files <PID>", "cat /proc/meminfo", "fuser -l <PID>"],
     "lsof = list open files; alternativ ls -l /proc/<PID>/fd. Wichtig u. a. für den Fall 'gelöschtes Log hält Platz fest'."),
    ("dateisystem", "Warum kann ein Hardlink nicht über Dateisystemgrenzen zeigen?",
     ["Inode-Nummern gelten nur innerhalb EINES Dateisystems — ein zweiter Name in einem anderen FS hätte keinen gültigen Bezug",
      "Aus Sicherheitsgründen von SELinux verboten",
      "Weil die Blockgrößen differieren können",
      "Er kann es — nur Symlinks sind beschränkt"],
     "Der Hardlink IST ein Verzeichniseintrag Name→Inode; Inodes sind pro Dateisystem nummeriert. Symlinks speichern dagegen nur einen Pfad-Text."),
    ("dateisystem", "Was bewirkt die umask 022?",
     ["Neue Dateien entstehen mit 644, Verzeichnisse mit 755 — Schreibrecht für Gruppe und Andere wird maskiert",
      "Alle neuen Dateien gehören root",
      "Neue Dateien sind ausführbar für alle",
      "Neue Dateien erben die Rechte des Verzeichnisses"],
     "umask zieht Bits von den Maximalrechten ab (Dateien 666, Verzeichnisse 777). 022 ist der übliche Default."),
    ("performance", "Welche Platte ächzt unter der Last? Das Werkzeug dafür?",
     ["iostat -x 1 — die %util-Spalte zeigt die Auslastung je Gerät", "df -h", "lsblk -f", "du -sh /"],
     "Nach dem %wa-Verdacht in top ist iostat der nächste Schritt: WELCHES Gerät ist der Engpass."),
    ("performance", "top zeigt hohen 'sy'-Anteil (System-CPU). Was heißt das?",
     ["Viel Zeit im Kernel — Syscalls, I/O-Verwaltung, Interrupts — statt in Anwendungsrechnung",
      "Das System swappt massiv",
      "systemd verbraucht die CPU",
      "Die CPU drosselt wegen Temperatur"],
     "us = Userspace-Arbeit, sy = Kernel-Arbeit, wa = Warten auf I/O. Hohes sy deutet oft auf I/O- oder Netzwerk-intensive Lasten."),
    ("ssh_user", "Wo liegen die für einen User erlaubten öffentlichen SSH-Schlüssel?",
     ["~/.ssh/authorized_keys", "~/.ssh/id_rsa", "/etc/ssh/ssh_host_keys", "~/.ssh/known_hosts"],
     "authorized_keys = wer darf SICH HIER anmelden; known_hosts = welchen SERVERN vertraue ich; id_* = meine eigenen Schlüssel."),
    ("ssh_user", "Welche Prozesse lauschen auf welchen Ports — der moderne Befehl?",
     ["ss -tulpen", "netstat -a (einzige Option)", "lsof -i --all", "ip port show"],
     "ss ist der netstat-Nachfolger: t=TCP, u=UDP, l=listening, p=Prozess, e=extended, n=numerisch."),
    ("patch", "Was ist eine CVE?",
     ["Eine öffentlich katalogisierte Sicherheitslücke mit eindeutiger Kennung (CVE-Jahr-Nummer) — die Währung des Security-Patchens",
      "Ein Red-Hat-internes Ticketformat",
      "Ein Zertifikat für geprüfte Pakete",
      "Die Versionsnummer eines Errata-Pakets"],
     "dnf updateinfo listet Advisories mit CVE-Bezug — so priorisiert man nach tatsächlichem Risiko."),
    ("patch", "Welcher Schritt kommt UNMITTELBAR vor dem Einspielen eines Patches in Prod?",
     ["Backup bzw. Snapshot — der vorbereitete Rollback", "Die Dokumentation schreiben", "needs-restarting ausführen", "Das Monitoring stummschalten"],
     "Hoffnung ist kein Rollback-Plan. Monitoring wird übrigens NICHT stummgeschaltet — es ist nachher die Verifikation."),
    ("selinux", "Warum ist chcon allein keine dauerhafte Lösung?",
     ["chcon ändert nur den Ist-Kontext; beim nächsten Relabel/restorecon stellt die Policy den alten Zustand wieder her — dauerhaft wird es erst mit semanage fcontext",
      "chcon wirkt nur bis zum nächsten Reboot",
      "chcon funktioniert nur im Permissive-Modus",
      "chcon kann keine Verzeichnisse rekursiv ändern"],
     "Ist-Zustand vs. Policy-Erwartung: semanage ändert die Erwartung, restorecon wendet sie an."),
    ("selinux", "Was bedeutet 'Default Deny' in der SELinux-Policy?",
     ["Was die Policy nicht ausdrücklich erlaubt, ist verboten — es braucht eine Regel FÜR jeden Zugriff",
      "Alle Zugriffe sind erlaubt, außer explizit verbotene",
      "Nur root-Prozesse sind eingeschränkt",
      "Neue Dateien sind bis zum Relabel gesperrt"],
     "Deshalb begrenzt SELinux den Schaden einer Kompromittierung: Der gekaperte Dienst hat nur die Regeln seines Typs."),
    ("systemd", "Unterschied systemctl mask vs. disable?",
     ["disable entfernt nur den Autostart; mask linkt die Unit auf /dev/null — sie kann auch manuell oder als Abhängigkeit nicht mehr starten",
      "mask ist die permanente Form von disable, sonst identisch",
      "disable stoppt den Dienst sofort, mask nicht",
      "mask wirkt nur bis zum Reboot"],
     "mask ist das 'wirklich nie' — z. B. für einen Altdienst, den nichts versehentlich wieder hochziehen darf."),
    ("systemd", "Welche Units sind nach dem Boot fehlgeschlagen?",
     ["systemctl --failed", "journalctl --units=failed", "systemctl status --all --errors", "dmesg | grep failed"],
     "Der schnelle Morgenblick nach einem Reboot — gern kombiniert mit journalctl -p err -b."),
    ("lvm", "Wozu ein LVM-Snapshot vor einem riskanten Change?",
     ["Ein eingefrorener Stand des LV als schneller Rollback — bei Fehlschlag zurückrollen statt restaurieren",
      "Er beschleunigt das Dateisystem während des Changes",
      "Er verdoppelt automatisch die Kapazität",
      "Er ersetzt das Backup dauerhaft"],
     "lvcreate -s. Wichtig: Snapshot ist Rollback-Werkzeug, kein Backup-Ersatz — er liegt auf demselben Storage."),
    ("lvm", "Was zeigt lsblk?",
     ["Den Blockgeräte-Baum: Platten, Partitionen, LVs und ihre Mountpoints auf einen Blick",
      "Nur die Belegung der Dateisysteme in Prozent",
      "Die Blockgröße jedes Dateisystems",
      "Defekte Sektoren der Platten"],
     "Der Orientierungsbefehl vor jeder Storage-Arbeit: Was hängt wo? Mit -f auch Dateisystem und UUID."),
    ("netz", "Was ist eine Rich Rule in firewalld?",
     ["Eine feinere Regel mit Quell-IP, Logging oder Rate-Limit — z. B. 'Port 5432 nur aus 10.0.2.0/24'",
      "Eine Regel, die mehrere Zonen gleichzeitig ändert",
      "Das firewalld-Pendant zu SELinux-Booleans",
      "Eine GUI-Vorlage für Standarddienste"],
     "Syntax nicht auswendig nötig — das Konzept (quellbasierte Feinregeln) reicht für Runde 1."),
    ("netz", "Welchen DNS-Resolver nutzt der RHEL-Host wirklich?",
     ["resolvectl status (bzw. Blick in /etc/resolv.conf)", "dig --resolver", "nmcli dns show", "cat /etc/hosts"],
     "Schritt 2 der DNS-Diagnose: Erst ob der Name auflöst (dig), dann WER ihn auflösen sollte."),
    ("ansible", "Was ist das Inventory?",
     ["Die Hostliste mit Gruppen ([webserver], [datenbanken]) — gegen wen Plays laufen",
      "Das Verzeichnis aller installierten Module",
      "Die Logdatei vergangener Playbook-Läufe",
      "Der Katalog der Ansible-Galaxy-Rollen"],
     "Play = Inventory-Gruppe × Tasks. Statt ssh-Schleifen über Hostnamen: Gruppen ansprechen."),
    ("ansible", "Warum im Handler 'state: reloaded' statt 'restarted', wo möglich?",
     ["reload lädt die Config ohne Verbindungsabbrüche; restart trennt aktive Clients — betriebsschonender ist reload",
      "restart ist in Handlern nicht erlaubt",
      "reload ist idempotent, restart nicht",
      "restart erfordert become: true, reload nicht"],
     "Dieselbe Rücksicht wie beim manuellen systemctl reload — Automatisierung übernimmt die guten Gewohnheiten."),
    ("itil", "Der Workaround greift, der Service läuft wieder. Ist damit alles erledigt?",
     ["Der Incident ja — aber ein Problem-Eintrag muss die Ursache weiterverfolgen, sonst kommt die Störung wieder",
      "Ja — Ticket schließen, fertig",
      "Nein — der Incident bleibt offen, bis die Root Cause behoben ist",
      "Nur wenn das Management zustimmt"],
     "Incident und Problem haben getrennte Lebenszyklen: Der Incident endet mit der Wiederherstellung, das Problem mit der Ursache."),
    ("itil", "Was gehört in eine brauchbare Incident-Dokumentation?",
     ["Zeitachse, Maßnahmen und ihre Wirkung — sofort geschrieben, denn die Problem-Analyse braucht Fakten statt Erinnerung",
      "Nur das Endergebnis in einem Satz",
      "Die Namen der Verantwortlichen für den Fehler",
      "Ein vollständiger Konfigurations-Dump aller Systeme"],
     "In zwei Wochen weiß es niemand mehr genau — und blamefrei heißt: Abläufe dokumentieren, nicht Schuldige."),

    # ---------------- tcpip (N1 Netzwerk-Grundlagen) ----------------
    ("tcpip", "TCP vs. UDP — der Kernunterschied und je ein typischer Einsatz?",
     ["TCP: verbindungsorientiert, bestätigt, in Reihenfolge — für Zuverlässigkeit (SSH, HTTPS); UDP: verbindungslos ohne Bestätigung — für Geschwindigkeit (DNS-Anfragen, NTP)",
      "TCP ist verschlüsselt, UDP unverschlüsselt",
      "UDP garantiert die Reihenfolge, TCP die Geschwindigkeit",
      "TCP läuft nur im LAN, UDP nur im Internet"],
     "Verlässlichkeit kostet Overhead (Handshake, ACKs, Retransmits). Wo ein verlorenes Paket egal oder schnell wiederholbar ist, gewinnt UDP."),
    ("tcpip", "Wie läuft der TCP-Drei-Wege-Handshake ab?",
     ["SYN → SYN-ACK → ACK — beide Seiten bestätigen Erreichbarkeit und tauschen Start-Sequenznummern, bevor Daten fließen",
      "HELLO → KEY → DATA",
      "SYN → ACK → FIN",
      "REQUEST → GRANT → CONFIRM"],
     "Deshalb zeigt ein Port-Scan 'offen', wenn ein SYN-ACK zurückkommt — und nc -zv testet genau diesen Handshake."),
    ("tcpip", "In welcher Reihenfolge löst ein RHEL-Host einen Hostnamen auf?",
     ["Wie /etc/nsswitch.conf es festlegt — üblicherweise erst /etc/hosts, dann der konfigurierte DNS-Resolver",
      "Immer zuerst DNS, /etc/hosts ist nur Fallback",
      "Alphabetisch über alle konfigurierten Quellen",
      "Über den ARP-Cache, dann DNS"],
     "Der Klassiker bei 'Name löst komisch auf': ein vergessener /etc/hosts-Eintrag gewinnt gegen DNS."),
    ("tcpip", "Wie besorgt sich ein Client per DHCP seine Adresse?",
     ["Discover → Offer → Request → Acknowledge (DORA) — Broadcast-Suche, Angebot, verbindliche Anfrage, Bestätigung mit Lease",
      "Request → Response in einem Schritt",
      "Der Server scannt das Netz und verteilt Adressen aktiv",
      "Login → Lease → Logout"],
     "Mit Lease-Zeit: Der Client erneuert rechtzeitig. DHCP-Probleme = oft doppelte Server oder abgelaufene Scopes."),
    ("tcpip", "Wozu VLANs?",
     ["Logische Segmentierung auf Layer 2: getrennte Broadcast-Domänen auf gemeinsamer Hardware — Sicherheit, Ordnung, kleinere Fehlerdomänen",
      "Schnellere Verkabelung zwischen Switches",
      "Verschlüsselung des LAN-Verkehrs",
      "Lastverteilung zwischen Routern"],
     "Zwischen VLANs führt der Weg nur über Routing/Firewall — genau da setzt deine OPNsense-Segmentierung an."),
    ("tcpip", "Was macht ein 802.1Q-Tag — und der Unterschied Trunk- vs. Access-Port?",
     ["Das Tag trägt die VLAN-ID im Ethernet-Frame: Ein Trunk transportiert mehrere VLANs getaggt, ein Access-Port genau eines, untagged",
      "Das Tag verschlüsselt den Frame zwischen Switches",
      "Trunk-Ports sind schneller, Access-Ports sicherer",
      "Das Tag ersetzt die MAC-Adresse im VLAN"],
     "Daher die klassische Störung: falsches/fehlendes Tagging am Trunk, und ein ganzes VLAN ist 'weg'."),
    ("tcpip", "Wie entscheidet ein Host, ob er ein Paket direkt zustellt oder ans Gateway schickt?",
     ["Er prüft per Subnetzmaske, ob das Ziel im eigenen Netz liegt: ja → direkt per ARP/MAC; nein → an das Default-Gateway",
      "Er fragt immer zuerst das Gateway",
      "Er schickt einen Ping und wertet die Antwortzeit aus",
      "Der DNS-Server teilt ihm die Route mit"],
     "Deshalb erzeugt eine falsche Maske so bizarre Fehler: Teile des eigenen Netzes gelten plötzlich als 'fern'. ip route get <ip> zeigt die Entscheidung."),
    ("tcpip", "Was leistet ARP?",
     ["Es löst IP-Adressen in MAC-Adressen im lokalen Segment auf — die Brücke von Layer 3 zu Layer 2",
      "Es verteilt IP-Adressen an neue Hosts",
      "Es löst Hostnamen in IP-Adressen auf",
      "Es prüft, ob ein Port offen ist"],
     "ip neigh zeigt den Cache. Doppelte IPs äußern sich als ARP-Flattern — zwei MACs streiten um eine Adresse."),
    ("tcpip", "Was ist ein PTR-Record?",
     ["Reverse-DNS: IP → Name — wichtig u. a. für Mailserver-Reputation und lesbare Logs",
      "Der Alias eines Hostnamens auf einen anderen",
      "Der Eintrag für den zuständigen Mailserver",
      "Die IPv6-Adresse eines Hosts"],
     "Die Familie: A (Name→IPv4), AAAA (→IPv6), CNAME (Alias), MX (Mail), PTR (rückwärts). dig -x <ip> fragt PTR ab."),
    ("tcpip", "Welche Adressbereiche sind privat (RFC 1918)?",
     ["10.0.0.0/8, 172.16.0.0/12 und 192.168.0.0/16",
      "127.0.0.0/8, 169.254.0.0/16 und 224.0.0.0/4",
      "Alle Bereiche unterhalb von 100.0.0.0",
      "10.0.0.0/8 und 8.8.8.0/24"],
     "Nicht im Internet routbar — darum NAT. (127/8 ist Loopback, 169.254/16 ist APIPA/Link-Local: das 'DHCP hat versagt'-Signal!)"),
    ("tcpip", "Wie funktioniert traceroute?",
     ["Es schickt Pakete mit steigender TTL; jeder Router, der die TTL auf 0 dekrementiert, meldet sich mit ICMP Time Exceeded — so wird der Pfad Hop für Hop sichtbar",
      "Es fragt jeden Router per SNMP nach seiner Routing-Tabelle",
      "Es pingt alle Hops gleichzeitig per Broadcast",
      "Es liest den Pfad aus dem DNS"],
     "Sternchen heißen: Hop antwortet nicht (ICMP gefiltert) — nicht zwingend 'kaputt'. Fürs Verständnis: TTL ist die Lebensdauer in Hops."),
    ("tcpip", "Was macht NAT (Source-NAT) am Netzrand?",
     ["Es übersetzt private Quelladressen auf die öffentliche IP — viele interne Hosts teilen sich eine externe Adresse, der Rückweg läuft über die Übersetzungstabelle",
      "Es verschlüsselt den ausgehenden Verkehr",
      "Es verteilt eingehende Anfragen auf mehrere Server",
      "Es blockiert private Adressen am Router"],
     "Konsequenz fürs Troubleshooting: Von außen 'sieht' man interne Hosts nicht — eingehende Dienste brauchen Port-Forwarding/DNAT."),
]

# ---------------------------------------------------------------------------
# Generator-Archetypen: deterministische Fragen aus Parameter-Pools.
# Jede Funktion bekommt rng und liefert (topic, frage, [richtig,*falsch], erkl).
# ---------------------------------------------------------------------------

def gen_oktal(rng):
    pool = [
        ("755", "rwxr-xr-x"), ("644", "rw-r--r--"), ("600", "rw-------"),
        ("700", "rwx------"), ("750", "rwxr-x---"), ("664", "rw-rw-r--"),
        ("640", "rw-r-----"), ("711", "rwx--x--x"), ("444", "r--r--r--"),
        ("770", "rwxrwx---"),
    ]
    oktal, symb = rng.choice(pool)
    falsch = [s for o, s in pool if s != symb]
    rng.shuffle(falsch)
    return ("dateisystem",
            "Welche symbolische Darstellung entspricht chmod %s?" % oktal,
            [symb] + falsch[:3],
            "r=4, w=2, x=1 je Tripel (User/Group/Other). %s = %s." % (oktal, symb))

def gen_oktal_rueck(rng):
    pool = [
        ("rwxr-xr-x", "755"), ("rw-r--r--", "644"), ("rw-------", "600"),
        ("rwxr-x---", "750"), ("rw-rw----", "660"), ("rwx--x--x", "711"),
        ("r-xr-xr-x", "555"), ("rwxrwxr-x", "775"),
    ]
    symb, oktal = rng.choice(pool)
    falsch = [o for s, o in pool if o != oktal]
    rng.shuffle(falsch)
    return ("dateisystem",
            "Eine Datei zeigt '%s'. Der passende Oktalwert?" % symb,
            [oktal] + falsch[:3],
            "Tripel einzeln addieren: %s = %s." % (symb, oktal))

def gen_load(rng):
    kerne = rng.choice([2, 4, 8, 16, 32])
    faktor = rng.choice(["unter", "etwa", "deutlich über"])
    if faktor == "unter":
        load = round(kerne * rng.choice([0.2, 0.4]), 1)
        richtig = "Unproblematisch — Load deutlich unter der Kernzahl, das System hat Reserven"
    elif faktor == "etwa":
        load = round(kerne * rng.choice([0.9, 1.0, 1.1]), 1)
        richtig = "Voll ausgelastet — Load ≈ Kernzahl; beobachten, Trend über 1/5/15-min prüfen"
    else:
        load = round(kerne * rng.choice([2.0, 3.0]), 1)
        richtig = "Stau — Load weit über der Kernzahl; mit top klären, ob CPU oder I/O-Wait (%wa) der Engpass ist"
    alle = [
        "Unproblematisch — Load deutlich unter der Kernzahl, das System hat Reserven",
        "Voll ausgelastet — Load ≈ Kernzahl; beobachten, Trend über 1/5/15-min prüfen",
        "Stau — Load weit über der Kernzahl; mit top klären, ob CPU oder I/O-Wait (%wa) der Engpass ist",
        "Load ist unabhängig von der Kernzahl zu bewerten",
    ]
    falsch = [a for a in alle if a != richtig]
    return ("performance",
            "Ein Server mit %d Kernen zeigt Load Average %.1f. Deine Bewertung?" % (kerne, load),
            [richtig] + falsch[:3],
            "Load immer relativ zu den Kernen lesen (nproc): %.1f auf %d Kernen = %.0f%% der Kapazität an laufwilligen Prozessen." % (load, kerne, 100.0 * load / kerne))

def _cmd_generator(name, topic, kontext, pool, merksatz):
    """Zwei-Richtungs-Drill: Aufgabe→Befehl und Befehl→Aufgabe."""
    def gen(rng):
        aufgabe, richtig, falsch = rng.choice(pool)
        if rng.random() < 0.5:
            f = list(falsch); rng.shuffle(f)
            return (topic, "%s: %s — welcher Befehl?" % (kontext, aufgabe),
                    [richtig] + f[:3], merksatz)
        else:
            andere = [a for a, _, _ in pool if a != aufgabe]
            rng.shuffle(andere)
            return (topic, "%s: Was bewirkt '%s'?" % (kontext, richtig),
                    [aufgabe] + andere[:3], merksatz)
    gen.__name__ = name
    return gen

gen_dnf = _cmd_generator("gen_dnf", "patch", "RHEL-Paketverwaltung", [
    ("verfügbare Updates nur ANZEIGEN, nichts ändern", "dnf check-update",
     ["dnf upgrade --dry", "dnf list --new", "dnf show-updates"]),
    ("nur sicherheitsrelevante Updates AUFLISTEN", "dnf updateinfo list security",
     ["dnf security list", "dnf list --cve", "dnf check-update --sec"]),
    ("nur Security-Updates EINSPIELEN", "dnf upgrade --security",
     ["dnf secure-update", "dnf upgrade --cve-only", "dnf install security"]),
    ("die letzte Transaktion rückgängig machen", "dnf history undo <ID>",
     ["dnf rollback", "dnf undo-last", "rpm --revert"]),
    ("prüfen, ob nach Updates ein Reboot nötig ist", "needs-restarting -r",
     ["dnf needs-reboot", "systemctl check-reboot", "uname --pending"]),
    ("herausfinden, welches Paket eine Datei liefert", "dnf provides /pfad/zur/datei",
     ["dnf whatis /pfad", "rpm --owner /pfad", "dnf search --file /pfad"]),
    ("alle installierten Kernel-Versionen auflisten", "rpm -q kernel",
     ["dnf list kernels", "uname -a --all", "ls /boot --kernels"]),
    ("Metadaten und Beschreibung eines Pakets ansehen", "dnf info <paket>",
     ["dnf describe <paket>", "rpm --about <paket>", "dnf show <paket>"]),
], "Werkzeugkasten: check-update (sichten), updateinfo (Security sichten), --security (gezielt patchen), history undo (Rollback), needs-restarting (Reboot-Frage).")

gen_selinux_cmd = _cmd_generator("gen_selinux_cmd", "selinux", "SELinux-Handwerk", [
    ("den aktuellen SELinux-Modus anzeigen", "getenforce",
     ["selinuxctl status", "semodule -s", "secon --mode"]),
    ("Status ausführlich inkl. Policy anzeigen", "sestatus",
     ["selinux --status", "getenforce -v", "semanage status"]),
    ("Kontexte von Dateien anzeigen", "ls -Z",
     ["ls --selinux", "getcon -f", "stat -c"]),
    ("die von der Policy erwarteten Kontexte eines Pfads wiederherstellen", "restorecon -Rv /pfad",
     ["chcon --reset /pfad", "semanage restore /pfad", "fixfiles now /pfad"]),
    ("einen Boolean dauerhaft setzen", "setsebool -P <boolean> on",
     ["setsebool --save <boolean>", "semanage bool -on <boolean>", "boolctl persist <boolean>"]),
    ("alle Booleans rund um httpd sichten", "getsebool -a | grep httpd",
     ["setsebool --list httpd", "semanage boolean --grep httpd", "ls -Z /etc/httpd"]),
    ("aktuelle Denials aus dem Audit-Log lesen", "ausearch -m AVC -ts recent",
     ["journalctl -u selinux", "grep AVC /var/log/messages", "sealert --tail"]),
    ("einen zusätzlichen Port für einen Dienst-Typ freigeben", "semanage port -a -t http_port_t -p tcp 8081",
     ["setsebool -P http_port_8081 on", "chcon -p tcp:8081 http", "firewall-cmd --selinux-port 8081"]),
], "Werkzeuggürtel: getenforce/sestatus, ls -Z, restorecon, semanage (fcontext/port), setsebool -P, ausearch.")

gen_journal = _cmd_generator("gen_journal", "systemd", "Journal-Handwerk", [
    ("Logs eines Dienstes live mitlesen", "journalctl -u <dienst> -f",
     ["journalctl --live <dienst>", "tail -f /var/log/<dienst>.log", "systemctl watch <dienst>"]),
    ("nur Meldungen des aktuellen Boots", "journalctl -b",
     ["journalctl --now", "journalctl --session", "dmesg --boot"]),
    ("Meldungen des VORHERIGEN Boots lesen (Crash-Analyse)", "journalctl -b -1",
     ["journalctl --last-boot", "journalctl -b 0", "journalctl --crash"]),
    ("nur Fehler und schlimmer, systemweit", "journalctl -p err",
     ["journalctl --errors", "journalctl -l error", "journalctl --severity=bad"]),
    ("alles der letzten Stunde", "journalctl --since \"1 hour ago\"",
     ["journalctl --last 1h", "journalctl -t 60m", "journalctl --recent"]),
    ("nur Kernel-Meldungen (wie dmesg)", "journalctl -k",
     ["journalctl --kernel-only", "journalctl -u kernel", "dmesg --journal"]),
    ("den Plattenverbrauch des Journals prüfen", "journalctl --disk-usage",
     ["journalctl --size", "du -sh /var/log/journal --live", "journalctl --quota"]),
], "Ein Werkzeug, eine Zeitachse: -u (Unit), -f (follow), -b/-b -1 (Boots), -p err (Priorität), -k (Kernel), --since (Zeitfenster).")

gen_firewall = _cmd_generator("gen_firewall", "netz", "firewalld-Handwerk", [
    ("die aktive Zone komplett anzeigen", "firewall-cmd --list-all",
     ["firewall-cmd --show", "firewall-cmd --zones --verbose", "firewall-cmd --status-all"]),
    ("https sofort, aber nur bis zum Reload erlauben", "firewall-cmd --add-service=https",
     ["firewall-cmd --add-service=https --permanent", "firewall-cmd --runtime-only https", "firewall-cmd --temp https"]),
    ("einen eigenen Port dauerhaft eintragen (noch nicht aktiv)", "firewall-cmd --add-port=8443/tcp --permanent",
     ["firewall-cmd --add-port=8443/tcp", "firewall-cmd --open 8443", "firewall-cmd --port 8443 --save"]),
    ("die permanente Konfiguration aktivieren", "firewall-cmd --reload",
     ["systemctl restart firewalld", "firewall-cmd --apply", "firewall-cmd --commit"]),
    ("alle aktiven Zonen und ihre Interfaces sehen", "firewall-cmd --get-active-zones",
     ["firewall-cmd --list-zones --active", "firewall-cmd --interfaces", "firewall-cmd --zone-map"]),
    ("die Standardzone abfragen", "firewall-cmd --get-default-zone",
     ["firewall-cmd --default", "firewall-cmd --zone", "firewall-cmd --show-default"]),
    ("einen Service dauerhaft wieder entfernen", "firewall-cmd --remove-service=samba --permanent",
     ["firewall-cmd --delete samba", "firewall-cmd --deny-service=samba", "firewall-cmd --drop samba --save"]),
], "Das Muster: runtime testen → --permanent schreiben → --reload aktivieren. Eingebauter Schutz vor Selbst-Aussperrung.")

gen_lvm_cmd = _cmd_generator("gen_lvm_cmd", "lvm", "Storage-Handwerk", [
    ("ein LV samt Dateisystem live um 10G vergrößern", "lvextend -r -L +10G /dev/vg/lv",
     ["lvresize --grow 10G /dev/vg/lv", "lvextend -L +10G /dev/vg/lv && reboot", "xfs_growfs +10G /dev/vg/lv"]),
    ("eine neue Platte für LVM vorbereiten", "pvcreate /dev/sdd",
     ["vgcreate /dev/sdd", "lvcreate --init /dev/sdd", "mkfs.lvm /dev/sdd"]),
    ("ein vorbereitetes PV in den bestehenden Pool aufnehmen", "vgextend <vg> /dev/sdd",
     ["pvextend <vg> /dev/sdd", "lvextend <vg> /dev/sdd", "vgadd /dev/sdd"]),
    ("freien Platz im Pool (VFree) prüfen", "vgs",
     ["pvs --free", "lvs --space", "df -h --vg"]),
    ("ein neues LV von 20G anlegen", "lvcreate -n daten -L 20G <vg>",
     ["vgcreate -n daten -L 20G", "mklv daten 20G <vg>", "lvnew --size 20G daten"]),
    ("alle LVs mit Größen anzeigen", "lvs",
     ["vgs --volumes", "lsblk --lvm-only", "pvdisplay --lv"]),
    ("die UUID eines Dateisystems für die fstab ermitteln", "blkid",
     ["uuidgen /dev/sdb1", "lsuuid", "fdisk --uuid"]),
], "Modell im Kopf: pvcreate (Zutat) → vgextend (Topf) → lvcreate/lvextend -r (Portion, wächst samt Dateisystem, live).")

gen_systemctl = _cmd_generator("gen_systemctl", "systemd", "systemd-Handwerk", [
    ("einen Dienst jetzt starten UND beim Boot aktivieren", "systemctl enable --now <dienst>",
     ["systemctl start --permanent <dienst>", "systemctl autostart <dienst>", "systemctl enable && reboot"]),
    ("dauerhaft ohne GUI booten", "systemctl set-default multi-user.target",
     ["systemctl disable graphical", "runlevel 3 --save", "grubby --no-gui"]),
    ("das aktuelle Default-Target abfragen", "systemctl get-default",
     ["systemctl --default", "systemctl show-target", "runlevel --default"]),
    ("alle aktiven Timer mit nächster Laufzeit sehen", "systemctl list-timers",
     ["systemctl --timers", "crontab -l --systemd", "timerctl list"]),
    ("geänderte Unit-Dateien neu einlesen", "systemctl daemon-reload",
     ["systemctl refresh", "systemctl reload-units", "systemctl rescan"]),
    ("eine Unit so sperren, dass sie auch manuell nicht startbar ist", "systemctl mask <dienst>",
     ["systemctl disable --force <dienst>", "systemctl lock <dienst>", "systemctl block <dienst>"]),
    ("eine Override-Anpassung an einer Paket-Unit anlegen", "systemctl edit <dienst>",
     ["vi /usr/lib/systemd/system/<dienst>.service", "systemctl override <dienst>", "systemctl patch <dienst>"]),
], "enable vs. start, edit statt /usr/lib anfassen, daemon-reload nach jeder Änderung, mask = wirklich nie.")

def gen_ports(rng):
    pool = [("SSH", "22"), ("HTTP", "80"), ("HTTPS", "443"), ("DNS", "53"),
            ("SMTP", "25"), ("NTP", "123"), ("PostgreSQL", "5432"),
            ("MySQL/MariaDB", "3306"), ("LDAP", "389"), ("RDP", "3389")]
    dienst, port = rng.choice(pool)
    if rng.random() < 0.5:
        falsch = [p for _, p in pool if p != port]
        rng.shuffle(falsch)
        return ("netz", "Standardport von %s?" % dienst, [port] + falsch[:3],
                "Die Klassiker gehören ins Sofortwissen: 22 SSH, 53 DNS, 80/443 Web, 25 SMTP, 123 NTP, 3306/5432 Datenbanken, 389 LDAP, 3389 RDP.")
    else:
        falsch = [d for d, p in pool if p != port]
        rng.shuffle(falsch)
        return ("netz", "Welcher Dienst lauscht standardmäßig auf Port %s?" % port,
                [dienst] + falsch[:3],
                "ss -tulpen zeigt, was wirklich lauscht — die Standardports sind die Lesebrille dafür.")

def gen_pfade(rng):
    pool = [
        ("die SSH-Server-Konfiguration", "/etc/ssh/sshd_config"),
        ("die Mount-Tabelle fürs Booten", "/etc/fstab"),
        ("die Passwort-Hashes", "/etc/shadow"),
        ("die sudo-Regeln", "/etc/sudoers"),
        ("der dauerhafte SELinux-Modus", "/etc/selinux/config"),
        ("die SELinux-Denials (Audit-Log)", "/var/log/audit/audit.log"),
        ("die GRUB-Einstellungen (Quelle, nicht generiert)", "/etc/default/grub"),
        ("die DNS-Resolver-Konfiguration", "/etc/resolv.conf"),
        ("eigene bzw. Override-systemd-Units", "/etc/systemd/system/"),
        ("die EFI System Partition (gemountet)", "/boot/efi"),
    ]
    was, pfad = rng.choice(pool)
    falsch = [p for _, p in pool if p != pfad]
    rng.shuffle(falsch)
    return ("dateisystem", "Wo liegt auf RHEL %s?" % was, [pfad] + falsch[:3],
            "Pfad-Sofortwissen spart im Störfall Minuten — und im Interview Zögern.")

def gen_ansible_mod(rng):
    pool = [
        ("ein Paket installieren", "ansible.builtin.dnf"),
        ("eine Config-Datei aus einer Vorlage mit Variablen rendern", "ansible.builtin.template"),
        ("einen Dienst starten und aktivieren", "ansible.builtin.service"),
        ("eine statische Datei auf die Hosts kopieren", "ansible.builtin.copy"),
        ("einen Benutzer anlegen", "ansible.builtin.user"),
        ("eine einzelne Zeile in einer Datei sicherstellen", "ansible.builtin.lineinfile"),
        ("einen Firewalld-Service freigeben", "ansible.posix.firewalld"),
    ]
    aufgabe, modul = rng.choice(pool)
    falsch = [m for _, m in pool if m != modul]
    rng.shuffle(falsch)
    return ("ansible", "Ansible: %s — welches Modul?" % aufgabe, [modul] + falsch[:3],
            "Module sind die idempotenten Könner; command/shell nur, wenn wirklich kein Modul passt — sonst verliert man die Idempotenz.")

def gen_subnet(rng):
    """CIDR-Drill: nutzbare Hosts, Netzmaske, Netz-/Broadcast-Adresse."""
    variante = rng.choice(["hosts", "maske", "netz", "broadcast"])
    if variante == "hosts":
        prefix = rng.choice([22, 23, 24, 25, 26, 27, 28, 29, 30])
        richtig = (2 ** (32 - prefix)) - 2
        falsch = {2 ** (32 - prefix), richtig // 2 if richtig > 2 else richtig + 4,
                  (2 ** (32 - prefix + 1)) - 2}
        falsch.discard(richtig)
        f = sorted(falsch)[:3]
        while len(f) < 3:
            f.append(richtig + 10 * (len(f) + 1))
        return ("tcpip", "Wie viele nutzbare Host-Adressen hat ein /%d-Netz?" % prefix,
                [str(richtig)] + [str(x) for x in f],
                "2^(32-%d) = %d Adressen, minus Netz- und Broadcast-Adresse = %d. Die Zweierpotenzen bis /22 gehören ins Sofortwissen." % (prefix, 2 ** (32 - prefix), richtig))
    if variante == "maske":
        pool = [22, 23, 24, 25, 26, 27, 28, 29, 30]
        prefix = rng.choice(pool)
        maske = str(ipaddress.ip_network("0.0.0.0/%d" % prefix).netmask)
        falsch = [str(ipaddress.ip_network("0.0.0.0/%d" % p).netmask)
                  for p in pool if p != prefix]
        rng.shuffle(falsch)
        return ("tcpip", "Welche Subnetzmaske entspricht /%d?" % prefix,
                [maske] + falsch[:3],
                "Pro Bit halbiert sich der Hostraum: /24=255.255.255.0, dann .128/.192/.224/.240/.248/.252 — die Treppe auswendig können.")
    # netz / broadcast: zufällige Host-IP in kleinem Netz, Blockrechnung
    prefix = rng.choice([25, 26, 27, 28, 29])
    basis = rng.choice(["192.168.%d" % rng.randrange(0, 255),
                        "10.%d.%d" % (rng.randrange(0, 255), rng.randrange(0, 255)),
                        "172.%d.%d" % (rng.randrange(16, 32), rng.randrange(0, 255))])
    block = 2 ** (32 - prefix)
    start = rng.randrange(0, 256 // block) * block
    offset = rng.randrange(1, block - 1)          # echte Host-Adresse
    ip = "%s.%d" % (basis, start + offset)
    netz = ipaddress.ip_network("%s/%d" % (ip, prefix), strict=False)
    if variante == "netz":
        richtig = str(netz.network_address)
        kand = {str(netz.broadcast_address), ip,
                "%s.%d" % (basis, (start + block) % 256),
                "%s.%d" % (basis, (start - block) % 256)}
        kand.discard(richtig)
        f = list(kand); rng.shuffle(f)
        return ("tcpip", "In welchem Netz liegt %s/%d (Netzadresse)?" % (ip, prefix),
                [richtig] + f[:3],
                "Blockgröße /%d = %d → Netzgrenzen bei Vielfachen von %d. %s fällt in den Block ab .%d." % (prefix, block, block, ip, start))
    else:
        richtig = str(netz.broadcast_address)
        kand = {str(netz.network_address), ip,
                "%s.%d" % (basis, (start + block) % 256),
                "%s.%d" % (basis, (start + block - 1 + block) % 256)}
        kand.discard(richtig)
        f = list(kand); rng.shuffle(f)
        return ("tcpip", "Wie lautet die Broadcast-Adresse des Netzes, in dem %s/%d liegt?" % (ip, prefix),
                [richtig] + f[:3],
                "Blockgröße %d, Block beginnt bei .%d → letzte Adresse des Blocks ist .%d = Broadcast." % (block, start, start + block - 1))

def gen_signal(rng):
    pool = [
        ("SIGTERM", "15", "höfliche Beendigung mit Aufräum-Chance — der Standard von kill und systemctl stop"),
        ("SIGKILL", "9", "sofortiges Entfernen durch den Kernel, kein Aufräumen — letzter Weg"),
        ("SIGHUP", "1", "Konvention bei Daemons: Konfiguration neu einlesen"),
    ]
    name, nr, bedeutung = rng.choice(pool)
    variante = rng.choice(["nr", "bedeutung"])
    if variante == "nr":
        falsch = [n for _, n, _ in pool if n != nr] + ["19"]
        rng.shuffle(falsch)
        return ("prozesse",
                "Welche Signalnummer hat %s?" % name,
                [nr] + falsch[:3],
                "%s (%s): %s." % (name, nr, bedeutung))
    else:
        falsch = [b for _, _, b in pool if b != bedeutung] + ["Prozess pausieren, bis SIGCONT kommt"]
        rng.shuffle(falsch)
        return ("prozesse",
                "Was bewirkt %s (%s) konventionell?" % (name, nr),
                [bedeutung] + falsch[:3],
                "Die drei fürs Interview: TERM 15 (höflich), KILL 9 (Kernel, letzter Weg), HUP 1 (Config-Reload).")

GENERATORS = [
    gen_oktal, gen_oktal_rueck, gen_load, gen_dnf,
    gen_selinux_cmd, gen_journal, gen_firewall, gen_lvm_cmd, gen_signal,
    gen_systemctl, gen_ports, gen_pfade, gen_ansible_mod, gen_subnet,
]

TOPIC_NAMEN = {
    "unix": "G1 Unix vs. Linux", "boot": "G2 Boot-Prozess",
    "prozesse": "G3 Prozesse & Signale", "dateisystem": "G4 Dateisystem & Rechte",
    "performance": "G5 Speicher & Last", "ssh_user": "G6 Benutzer, SSH & Shell",
    "patch": "K1 Patchmanagement", "selinux": "K2 SELinux", "systemd": "K3 systemd & Boot-TS",
    "lvm": "K4 Storage & LVM", "netz": "K5 Netzwerk & firewalld",
    "ansible": "K6 Ansible", "itil": "K7 ITIL & Incident",
    "tcpip": "N1 TCP/IP, DHCP & VLANs",
}

# ---------------------------------------------------------------------------

def frage_fuer_seed(seed, topic=None):
    """Pure Funktion: Seed (+ optionaler Topic-Filter) -> Frage-Dict."""
    rng = random.Random(seed)
    statik = [q for q in STATIC if topic is None or q[0] == topic]
    gens = [g for g in GENERATORS
            if topic is None or g(random.Random(0))[0] == topic]
    # Mischverhältnis: Statik dominiert, Generatoren liefern Drill-Varianten.
    if gens and (not statik or rng.random() < 0.35):
        t, f, opts, erkl = rng.choice(gens)(rng)
    else:
        t, f, opts, erkl = rng.choice(statik)
    opts = list(opts)
    richtig = opts[0]
    rng.shuffle(opts)
    return {"topic": t, "frage": f, "optionen": opts,
            "richtig_idx": opts.index(richtig), "erkl": erkl}

def stelle_frage(seed, nummer=None, gesamt=None, topic=None):
    """Interaktiv eine Frage stellen. Rückgabe: (korrekt: bool, topic)."""
    q = frage_fuer_seed(seed, topic)
    kopf = "— Frage"
    if nummer and gesamt:
        kopf += " %d/%d" % (nummer, gesamt)
    kopf += "  [Seed %d · %s] " % (seed, TOPIC_NAMEN.get(q["topic"], q["topic"]))
    print()
    print(kopf + "—" * max(1, 74 - len(kopf)))
    print(q["frage"])
    print()
    buchstaben = "abcd"
    for i, opt in enumerate(q["optionen"]):
        print("  %s) %s" % (buchstaben[i], opt))
    while True:
        try:
            antwort = input("\nDeine Antwort [a-d, q=Ende]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None, q["topic"]
        if antwort == "q":
            return None, q["topic"]
        if antwort in buchstaben[:len(q["optionen"])]:
            break
        print("Bitte a, b, c oder d.")
    korrekt = buchstaben.index(antwort) == q["richtig_idx"]
    if korrekt:
        print("✓ RICHTIG.")
    else:
        print("✗ FALSCH. Richtig: %s) %s"
              % (buchstaben[q["richtig_idx"]], q["optionen"][q["richtig_idx"]]))
    print("→ " + q["erkl"])
    return korrekt, q["topic"]

def session(seeds, topic=None):
    """Eine Serie von Seeds abfragen; Score, Themenbilanz, Repeat-Stapel."""
    ergebnisse, falsche = [], []
    for n, seed in enumerate(seeds, 1):
        korrekt, t = stelle_frage(seed, n, len(seeds), topic)
        if korrekt is None:          # Abbruch mit q / Ctrl-C
            break
        ergebnisse.append((korrekt, t))
        if not korrekt:
            falsche.append(seed)
    if not ergebnisse:
        return
    richtig = sum(1 for k, _ in ergebnisse if k)
    print()
    print("=" * 74)
    print("Ergebnis: %d/%d richtig (%d%%)"
          % (richtig, len(ergebnisse), round(100.0 * richtig / len(ergebnisse))))
    themen = {}
    for k, t in ergebnisse:
        r, g = themen.get(t, (0, 0))
        themen[t] = (r + (1 if k else 0), g + 1)
    schwach = [(t, r, g) for t, (r, g) in sorted(themen.items()) if r < g]
    if schwach:
        print("Nacharbeiten (Kapitel im Lernguide):")
        for t, r, g in schwach:
            print("  %-28s %d/%d" % (TOPIC_NAMEN.get(t, t), r, g))
    if falsche:
        cmd = "python3 quiz.py --seeds " + " ".join(str(s) for s in falsche)
        if topic:
            cmd += " --topic " + topic
        print("Dein Repeat-Stapel für morgen:")
        print("  " + cmd)
    print("=" * 74)

def liste():
    print("Themen (--topic <name>):")
    gesamt = 0
    for t in TOPIC_NAMEN:
        n = sum(1 for q in STATIC if q[0] == t)
        gesamt += n
        gen = [g.__name__ for g in GENERATORS
               if g(random.Random(0))[0] == t]
        zusatz = "  + Generator: %s" % ", ".join(gen) if gen else ""
        print("  %-12s %-26s %3d statisch%s" % (t, TOPIC_NAMEN[t], n, zusatz))
    print("Gesamt: %d statische Fragen + %d Generator-Archetypen mit Parameter-Pools"
          % (gesamt, len(GENERATORS)))
    print("Distinkter Fragenraum: 712 gemessen über die Seeds 1-30000.")

def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return 0
    topic = None
    if "--topic" in argv:
        i = argv.index("--topic")
        if i + 1 >= len(argv):
            print("--topic braucht einen Namen. Verfügbar: %s"
                  % ", ".join(TOPIC_NAMEN))
            return 1
        topic = argv[i + 1]
        del argv[i:i + 2]
        if topic not in TOPIC_NAMEN:
            print("Unbekanntes Thema '%s'. Verfügbar: %s"
                  % (topic, ", ".join(TOPIC_NAMEN)))
            return 1
    if "--list" in argv:
        liste()
        return 0
    if "--seeds" in argv:
        i = argv.index("--seeds")
        try:
            seeds = [int(x) for x in argv[i + 1:]]
        except ValueError:
            print("--seeds erwartet Zahlen, z. B.: python3 quiz.py --seeds 42 881 17")
            return 1
        if not seeds:
            print("--seeds erwartet mindestens eine Zahl.")
            return 1
        session(seeds, topic)
        return 0
    if "--exam" in argv:
        start = random.SystemRandom().randrange(1, 10 ** 6)
        print("Exam-Session, Start-Seed %d (Replay: python3 quiz.py --seeds %s)"
              % (start, " ".join(str(start + k) for k in range(25))))
        session([start + k for k in range(25)], topic)
        return 0
    if "--run" in argv:
        i = argv.index("--run")
        anzahl = int(argv[i + 1]) if len(argv) > i + 1 and argv[i + 1].isdigit() else 10
        start = random.SystemRandom().randrange(1, 10 ** 6)
        session([start + k for k in range(anzahl)], topic)
        return 0
    rest = [a for a in argv[1:] if not a.startswith("-")]
    if rest:
        try:
            seed = int(rest[0])
        except ValueError:
            print("Unbekanntes Argument '%s' — Hilfe: python3 quiz.py --help" % rest[0])
            return 1
        bare = False
    else:
        seed = random.SystemRandom().randrange(1, 10 ** 6)
        bare = topic is None
    ergebnis = stelle_frage(seed, topic=topic)
    if ergebnis[0] is False:
        print("Replay: python3 quiz.py %d%s"
              % (seed, (" --topic " + topic) if topic else ""))
    if bare:
        print("Tipp: Sessions mit 'python3 quiz.py --run 20', themenweise mit "
              "'--topic selinux' (alle Themen: --list, Hilfe: --help).")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
