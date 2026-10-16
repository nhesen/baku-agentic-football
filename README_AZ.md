# Baku FC V4 — 5v5 düzülüş araşdırması

Bir GK və dörd meydan oyunçusu. Bu, şərti qaydalar + istəyə bağlı LLM menyu seçimidir; yenidən təlim edilmiş çempion neyron şəbəkəsi deyil.

Native rəqibə qarşı bu yekun dəstdə qələbə sayı artmadı. Daha yüksək qələbə faizi əldə etdiyimizi iddia etmirik.

Yekun oyunlarda zəifləmə aşkarlandığı üçün əsas təqdimat profilində əvvəlki V3 hücum davranışı saxlandı (`formation: original`, 1–1–2-yə yaxın mobil quruluş). 2–1–1 ayrıca eksperimental profildə saxlanıb. Bu, testdən sonra parametr sazlaması deyil, zəif namizədin geri qaytarılmasıdır. Yeni versiyanı qələbə artımı kimi təqdim etmirik.

Yerli matç nəticələri və bütün məhdudiyyətlər `reports/NETICELER_AZ.md` içindədir. AWS profili və beş yerli runtime paketi hazırlanıb, canlı AWS-də yoxlanmayıb.

`profiles/agentpitch-validated.json`: əsas yerli profil. `profiles/agentpitch-experimental-2-1-1.json`: doğrulama qalibi, eksperimental. `profiles/aws-candidate.json`: uyğunlaşdırılmalı bulud namizədi. Əsas settings AWS namizədidir.

Sınaqlar: `python -m unittest discover -s tests` (paket qovluğundan). Yerli qurma: `python tools/build_agents.py`. Bu əmrlər deploy etmir.
