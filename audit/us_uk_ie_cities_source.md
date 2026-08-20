# US, UK, and IE draft city pages source notes

Checked date: 2026-08-19

These city lists were user-confirmed before implementation. The sources below support the selection logic: large population centers, regional healthcare markets, and broad English-language marketplace coverage. They do not provide provider, address, price, test, or availability data, and none of those fields were added.

## US

Source: U.S. Census Bureau, "Population Growth Holds Steady in Midsized Cities Amid Widespread Slowdown", https://www.census.gov/newsroom/press-releases/2026/vintage-2025-city-town-pop-estimates.html

Source: U.S. Census Bureau, "Population Growth Reported Across Cities and Towns in All U.S. Regions", https://www.census.gov/newsroom/press-releases/2025/vintage-2024-popest.html

- New York, NY: included as the largest U.S. city in Census city population estimates.
- Los Angeles, CA: included as one of the largest U.S. cities in Census city population estimates.
- Chicago, IL: included as one of the largest U.S. cities in Census city population estimates.
- Houston, TX: included as one of the largest U.S. cities in Census city population estimates.
- Phoenix, AZ: included as one of the largest U.S. cities in Census city population estimates.
- Miami, FL: included from the user-confirmed shortlist as a major Florida/South Florida market; Census city estimates also identify Miami among cities with large recent numeric population growth.

## UK

Source: Office for National Statistics, "Population dynamics of UK city regions since mid-2011", https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/articles/populationdynamicsofukcityregionssincemid2011/2016-10-11

Source: Centre for Cities, "City monitor: The latest data", https://www.centreforcities.org/reader/big-cities-outlook-2026/city-monitor-the-latest-data/

- London: included as the largest UK city region and a major national healthcare market.
- Manchester: included as a major Greater Manchester city region market.
- Birmingham: included as the key city for the West Midlands city region market.
- Leeds: included as the key city for the West Yorkshire city region market.
- Glasgow: included as a major Scottish city region market.
- Bristol: included as a major South West England city region market.

## IE

Source: Central Statistics Office Ireland, "Census of Population 2022", https://www.cso.ie/en/statistics/population/censusofpopulation2022/

Source: Central Statistics Office Ireland, "Population and Age Ireland and Northern Ireland - A Joint Census Publication 2021-2022", https://www-cloud.cso.ie/en/releasesandpublications/ep/p-cpini/irelandandnorthernireland-ajointcensuspublication2021-2022/populationandage/

Source: Houses of the Oireachtas, written answer table citing Census 2022 city and suburb populations, https://www.oireachtas.ie/en/debates/question/2024-09-09/section/711/

- Dublin: included as Ireland's largest city/capital market.
- Cork: included as a major Irish city and county market.
- Galway: included as a major west-of-Ireland city market.
- Limerick: included as a major Mid-West city and county market.
- Waterford: included as a major south-east city and county market.

Region-field note: IE `region` values intentionally follow the most useful local-area label for this minimal schema. Dublin has no single county local authority, while Cork and Galway have separate city and county councils with different boundaries; for this draft location schema, the shorter city-market labels remain clearer than forcing a county label. Limerick and Waterford use `Limerick City and County` and `Waterford City and County`, reflecting their unified city-and-county authorities.
