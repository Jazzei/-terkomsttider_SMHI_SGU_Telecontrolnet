Applikation är tänkt att koppla upp mot Telecontrolnets API och hämta data från alla tillgängliga GDTer (grundvattennivåmätare) och visualisera data.

Användaren ska kunna välja vilken GDT som ska visualiseras och även välja vilken tidsperiod som ska visualiseras. Det vill säga applikationen ska okcså 
kunna visualisera data från Telecontrolnet, SGU och SMHI. (sannolikt behövs observations- och referensdata normaliseras innan alternativt att introducera en extra y axel)

Applikationen ska spara data i en lokal databas för att kunna arbeta offline.

Applikationen ska ha förmågan att korrigera felaktiga observationer. Detta då GDTn (sensorn) kan ha varit installerad i flera brunnar. Vidare kan data vara felaktig då 
den inte kompenserats gentemot rörets över kant innan registering av data påbörjas.

Applikationen ska kunna hämta data från SGU, referensdata som i sin tur kan användas för att beräkna återkomsttiden 50 - 100 år för grundvattennivån i observationsrören.

Applikationen ska kunna beräkna avstånd mellan WSG84 koordinater, samt kunna konvertera SWEREF99TM koordinater till WSG84 koordinater.

Applikationen ska ta hänsyn till referenserörens höjd över havet / bedömd läge i akvifär (samt topografiskt läge för observationsröret) och endast jämföra lämpliga observationsrör
och referenserör.

Applikationen ska kunna hämta data från SMHI och visualiser nederbördsdata från den närmaste väderstationen intill observationsröret. 


Applikationen ska kunna använda sig av atmosfärens tidsvågor https://hess.copernicus.org/articles/27/3447/2023/ för att kunna beräkna akvifär egenskaper. Prioritet mycket låg.


En del av arbetet har gjort och funktionerna finner du i src/ groundwater_calculation.py, telecontrolnet.py, smhi.py, sgu.py och coordinate_converter.py.



*TO-DO*



Telecontrolnet:

    - Observationsdata från Telecontrolnet ska lagras i lokal databas (vilken databasen är lämpligast SQLite?). Prioritet hög.

    - Inkludera även lufttrycksdata från Telecontrolnet. Priotet låg.

    - Användar filtrer av observationsdata, flertalet av observationerna är inte relevanta det ska vara enkelt att ta bort data. Detta då GDTerna (sensorn) kan ha varit installerad i flera brunnar. Därmed återspeglar en del av observationerna inte grundvattennivån i nuvarande observationsbrunn. En del av observationerna är även felaktiga då de inte kompenserats gentemot rörets över kant. Prioritet medel.

    Detta är ett stort dataset. För att kunna beräkna återkomsttider enligt Chalmersmodellen i alla lämpliga observationsrör behövs bra 
    filter för observationsdata. Chalmersmodellen kanske inte är den bästa metoden men en standard i geoteknik om inte långa tidserier för att 
    beräkna dimiensioneradefinns grundevattennivå. Efter 3 månader med med två observationer i månaden går det att passa data mot lämpligt SGU referensrör. 


SGU:

    - Hitta lämpliga referensrör och lagra i en lokal databas. Prioritet hög.

SMHI:

    - Nederbördsdata från SMHI ska hämtas och lagras i en lokal databas. (Möjligen lufttryck och temperatur också) Prioritet låg.

coordinate_converter:

    - 

    

    Referensdata från SGU ska hämtas och lagras i en databas.

    - Lagra anropet från SGU (sgu.py) och lagra i databasen.


Utveckling 


   '''
                        If p ≤ α: Reject the null hypothesis. Conclude that there is a significant linear correlation.
                        If p > α: Fail to reject the null hypothesis. Conclude that there is not enough evidence to support 
                        a significant linear correlation. In summary, the p-value in Pearson correlation helps researchers 
                        and analysts determine whether the observed correlation between two variables is statistically 
                        significant or if it could have occurred by random chance under the assumption of no true correlation.
                        '''