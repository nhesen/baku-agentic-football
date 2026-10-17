# Baku FC V7 — 5v5 zərbə və ötürmə düzəlişləri

Bir qapıçı və dörd meydan oyunçusu. V7 bloklu zərbə seçimini, cinahdan mərkəzə geriyə ötürmə prioritetini və rəqib buraxılışından sonra örtüyü ayrı modullar kimi əlavə edir.

Yeni variant qəbul şərtini keçmədi; əsas profil V6 matç davranışını saxlayır. Yeni düzəlişlər ayrıca profillərdədir.

## Davranışlar

- Zərbə dəhlizi filtri həm qərar menyusunda, həm müstəqil validatorda tətbiq edilir; açıq uzaq zərbələr saxlanılır.
- Yalnız açıq, qapıya daha yaxın mərkəzi qəbul nöqtəsinə cutback pası top sürmədən önə çəkilə bilər.
- Rəqib topu buraxdıqdan sonra ən çox 1.5 saniyəlik örtük yaddaşı; oyun vaxtı yoxdursa yeni timed örtük qurulmur.
- Pas ehtimalı modelinin `flow` sxeminə qoşulması düzəlib; matç üstünlüyü yoxlanmadığı üçün əsas profildə söndürülüb.
- Give-go yaddaşı, örtüklü press yaxınlaşması, öz pasının qəbul nöqtəsi, ofsayd, restart və cooldown qoruyucuları saxlanılıb.

[Dəqiq qaydalar və profil izahları](PATCHES_AZ.md). [Göndərilmiş patch-in baxışı](docs/V7_PATCH_REVIEW_AZ.md).

## Nəticələr

148 tam nəzarətli native matç: 4 uyğunluq təkrarı, 40 ilkin seçim, 24 doğrulama və 80 əvvəl görünməmiş yekun oyun. Hər iki tərəfdə callback xətası və engine fallback sayı sıfırdır. Saat qorumasından əvvəlki 36 tamamlanmış pilot oyunu ayrıca saxlanılıb, əsas statistikaya qatılmayıb.

| Variant / rəqib | Oyun | Q | H | M | Qollar |
|---|---:|---:|---:|---:|---:|
| e_off / baseline | 20 | 1 | 17 | 2 | 2:3 |
| e_cutback / baseline | 20 | 1 | 17 | 2 | 2:3 |
| e_off / reference6 | 20 | 3 | 14 | 3 | 3:3 |
| e_cutback / reference6 | 20 | 3 | 14 | 3 | 3:3 |

Seçilmiş yeni namizəd `e_cutback`. Ümumi qələbə fərqi 0 faiz bəndi, cüt toxum bootstrap 95% intervalı [0.0, 0.0]. Canlı AWS turnirinin qələbə ehtimalı deyil.

- [Tam nəticələr](reports/finishing-v7/NETICELER_AZ.md)
- [148 matçın cədvəli](reports/finishing-v7/ALL_MATCHES.csv)
- [Faktiki hücum göstəriciləri](reports/finishing-v7/DIAGNOSTICS.json)
- [Qol epizodları](reports/finishing-v7/GOAL_AUDIT.json)
- [Yekun matçın təkrarı](reports/finishing-v7/replay-first.html)
- [Əvvəlki V6 nəticələri](reports/coaching-v6/NETICELER_AZ.md)

## İşlətmək

```sh
python -m venv .venv
python -m pip install -r requirements-runtime.txt
python -m pip install httpx
python -m unittest discover -s tests
python tools/build_agents.py
```

**85 test keçib, ötürülən yoxdur.** Beş runtime yerli qurulub, mənbə və settings baytları yoxlanıb. Build AWS deploy etmir.

Əsas yerli profil: `profiles/agentpitch-validated.json`. Parametrlər: `phase_tactics=attack`, `combination_tactics=give_go`, `finishing_tactics=off`. Native fingerprint: `7d83678780179e5c`.

`profiles/finish-*.json` rejimləri: `off`, `shot`, `cutback`, `cover`, `balanced`. `profiles/optional-retention.json` modelin texniki qoşulmasını açır; bu V7 matç seriyasında onun qələbə üstünlüyü ölçülməyib. Modelin AUC-si qol və ya qələbə ehtimalı deyil.

AWS namizədi: `profiles/aws-candidate.json` və `baku_fc/settings.json`; 110×70 meydan fərziyyəsi və canlı model seçimi var, canlı AWS-də yoxlanmayıb. Native müqayisə 100×60 meydanda, eyni fizika/atributlarla, hər oyunda 1200 tick, iki tərəfdən aparılıb. Rəqiblər native baseline və dondurulmuş V6 agentimizdir. AWS çempionlarının agentləri istifadə edilməyib.

## Mənşə

Öz kodu və AWS şablonu MIT-0, təkrarlardakı upstream AgentPitch viewer Apache-2.0-dır. [Mənbələr](SOURCES.json), [bildirişlər](third_party/README.md), [sınaq mənşəyi](reports/finishing-v7/PROVENANCE.json). Xam matç ZIP-i yerli outputs/baku-v7-study qovluğundadır.
