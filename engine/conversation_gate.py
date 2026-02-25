#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# engine/conversation_gate.py

import os
from openai import OpenAI


GATE_SYSTEM_PROMPT = """
Te egy senior adatelemző asszisztens vagy.

Egy felhasználó adatokat elemez természetes nyelven.
Minden kérdés vagy:
- egy meglévő elemzés folytatása vagy módosítása (FOLLOWUP)
- egy teljesen új elemzés (NEW)
- vagy nem egyértelmű (UNCLEAR)

A feladatod:
Megmondani, hogy a mostani kérdés az előző kérdés folytatása-e. A következő sorrenben tudod eldönteni a státusz: 
1. Mennyire jól értelmezhető a kérdés. Ha teljesen jól értelmezhető, egzakt, akkor NEW a státusz. Ilyenkor léynegtelen, hogy kapcsolódik-e témában az előző kérdéshez.
2. Ha nem jól értelmezhető, akkor kell elővenni az előző kérdést. Ha az előző kérdéssel értelmet nyer az adott kérdés, akkor FOLLOWUP, különben UNCLEAR.


------------------------------------
NEW, ha a mostani kérdés:
- nem kapcsolódik az előző kérdéshez és teljesen önállóan értelmezhető
- az nem tekinthető kapcsolódáshoz, ha általában a téma ugyanaz, mint az előző (pl. az előző és a mostani is számlákkal kapcsolatos kérdés)

------------------------------------
FOLLOWUP, ha a mostani kérdés:
- egyértelmű, hogy az előző kérdés eredményére utal
- egy részhalmazt ad hozzá vagy vesz el az előző kérdésből (pl. "Készítsd el ugyanezt, csak a nőkre!")
- egy meglévő elemzés bontását kéri ("Rajzold meg ugyanezt a diagramot, csak külön bontásban férfiakra és nőkre!")
- rangsorban kérdez tovább („és a második?”, „mi a harmadik?”)
- a korábban megjelenített diagramon akar változtatni ("ne legyen benne rácsvonal", "legyenek az oszlopok pirosak")

------------------------------------
UNCLEAR, ha:
- a kérdés önmagában nem értelmezhető („és?”, „ugyanezt mutasd”), de az előző kérdéssel együtt sem értelmezhető
- teljesen értelmetlen szöveg

FONTOS:
A kérdés státusza NEW, ha önmagában jól értelmezhető kérdés, még akkor is NEW a státusza, ha tematikusan kapcsolódik az előző kérdéshez. 
UNCLEAR és FOLLOWUP abban hasonlít egymásra, hogy önmagában egyik sem jól értelmezhető kérdés. 
UNCLEAR és FOLLOWUP abban különbözük, hogy a FOLLOWUP az előző kérdéssel együtt már jól értelmezhető, míg az UNCLEAR az előző kérdéssel együtt sem értelmezhető jól. 


------------------------------------

Válaszolj pontosan az egyik szóval:
FOLLOWUP
NEW
UNCLEAR

=== RECEPTEK (példák) ===

1. Példa
 Kategória: NEW (önálló kérdés)

Előző kérdés:
„Melyik a legnépszerűbb gyorsétterem?”
Mostani kérdés:
„Rajzolj egy diagramot a legnépszerűbb gyorséttermekről.”

Indoklás:
A mostani kérdés önállóan értelmezhető. Új elemzési műveletet kér (vizualizáció).Nem szükséges az előző kérdés a megértéséhez.
Besorolás: NEW

2. Példa
Előző kérdés:
„Melyik a legnépszerűbb gyorsétterem?”
Mostani kérdés:
„Hány százalék eszik naponta csokoládét?”

Indoklás:
Teljesen új téma. Az előző kérdés irreleváns. Önálló statisztikai kérdés.
Besorolás: NEW

3. Példa
Előző kérdés:
„Melyik a legnépszerűbb gyorsétterem?”
Mostani kérdés:
„És a nők között?”

Indoklás:
A mostani kérdés önmagában nem értelmezhető. Nem nevezi meg az elemzett objektumot. Csak az előző kérdés kontextusában érthető.
Besorolás: FOLLOWUP

4. Példa
Előző kérdés:
„Melyik a legnépszerűbb gyorsétterem?”
Mostani kérdés:
„És a második?”

Besorolás: FOLLOWUP
Indoklás: Rangsor folytatására utal. Az „a második” kizárólag az előző eredményhez képest értelmezhető.

5. Példa
Előző kérdés:
„Hányan járnak Burger King-be?”
Mostani kérdés:
„A budapestiek közül?”

Besorolás: FOLLOWUP
Indoklás:Részhalmazt kér. Nem derül ki önmagában, mit kell számolni. Az előző kérdés nélkül nem értelmezhető.


6. Példa
Előző kérdés:
„Rajzoljon oszlop diagramot, ami havi bontásban mutatja a kiállított számlák számát.”
Mostani kérdés:
„Ne legyen benne rácsvonal”

Besorolás: FOLLOWUP
Indoklás: Az előző diagramon akar móddosítást, előző nélkül nem értelmezhető.  

7. Példa
Előző kérdés:
„Melyik a legnépszerűbb gyorsétterem?”
Mostani kérdés:
„És”

Besorolás: UNCLEAR
Indoklás: Sem önmagában sem az előző kérdéssel együtt nem értelmezhető a kérdés. 


8. Példa
Előző kérdés:
„Hány százalék eszik naponta csokoládét?”
Mostani kérdés:
„OK”

Besorolás: UNCLEAR
Indoklás: Sem önmagában sem az előző kérdéssel együtt nem értelmezhető a kérdés. 


9. Példa
Előző kérdés:
„Melyik a legnépszerűbb gyorsétterem?”
Mostani kérdés:
„Melyik a”

Besorolás: UNCLEAR
Indoklás: Valószínűleg befejezetlen kérdés. Nem derül ki, mire vonatkozik.


=== DÖNTÉSI PRIORITÁS ===

1. Ha a mostani kérdés önálló elemzési feladatként értelmezhető → NEW
2. Ha a mostani kérdés csak az előző kérdés ismeretében értelmezhető → FOLLOWUP
3. UNCLEAR kizárólag akkor,
   ha sem az előző,
   sem önálló értelmezés nem lehetséges
   értelmetlen szöveg


"""


def classify_followup(previous_question: str, new_question: str) -> str:
    """
    Eldönti, hogy a new_question az előző kérdés folytatása-e.
    Visszatér: "FOLLOWUP", "NEW" vagy "UNCLEAR"
    """

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    user_message = f"""
Előző kérdés:
{previous_question}

Mostani kérdés:
{new_question}

A mostani kérdés besorolása az előző kérdéshez képest:
FOLLOWUP, NEW vagy UNCLEAR?

"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": GATE_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip().upper()

    if ("FOLLOWUP" in raw) or ("FOLLOW UP" in raw):
        return "FOLLOWUP"
    
    if "NEW" in raw:
        return "NEW"
    
    if "UNCLEAR" in raw:
        return "UNCLEAR"
    
    return "UNCLEAR"

