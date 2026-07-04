\# DFS Database Design



\## Purpose



The purpose of the DFS database is to store Babylon 5: A Call to Arms Second Edition ship data in a structured format that allows the automatic generation of professional-quality printable ship sheets.



The database will be designed to support future expansion, but Version 0.1 is focused solely on Babylon 5 ACTA Second Edition.



\---



\# Design Principles



\## 1. Ship Sheet First



Every design decision should support the creation of accurate and attractive ship sheets.



\## 2. Single Source of Truth



Information should exist in only one logical location whenever practical.



\## 3. Keep It Simple



The database should solve today's problem without unnecessarily complicating future development.



\## 4. Expand Without Rebuilding



The schema should allow future expansion into additional game systems without requiring a complete redesign.



\---



\# Version 0.1 Scope



Version 0.1 supports:



\- Babylon 5: A Call to Arms Second Edition

\- Ship entry

\- Ship editing

\- Ship sheet generation

\- PDF/Print output



Version 0.1 does not include:



\- Fleet building

\- Campaign management

\- Additional game systems

\- Online sharing

\- Community features



\---



\# Core Objects



\## Ship



A Ship represents the physical vessel itself.



Examples:



\- Omega Destroyer

\- Hyperion Cruiser

\- Sharlin War Cruiser



A Ship is the permanent identity of the vessel.



For Version 0.1, a Ship contains information that identifies the vessel but does not contain ACTA game statistics.



ACTA game statistics belong to the Ship's ACTA Profile.

