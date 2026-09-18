# Progress: archive RealPage-target material

## T1 ✅ Write check-no-realpage-target.sh 

**What:** Created bash script `tooling/check-no-realpage-target.sh` that identifies RealPage-as-target (customer pitch) references while allowing:
- RealPage as a software brand in data files (leads.json, rules.json, detector rules)
- RealPage in vendor comparison lists (alongside Yardi, Entrata, AppFolio)
- RealPage in outside-in research context
- Color mappings for RealPage as a vendor
- Python docstrings

**Violations found:** 40 lines that position RealPage as target customer or internal project identifier (like "RealPage Discord thread", "for RealPage", "Where RealPage already has clients")

**How checked:** Ran `bash tooling/check-no-realpage-target.sh` → exits non-zero with list of 40 violations to remediate in T2-T9

**Commit:** [pending below]

**Next:** T2 moves research folders and case study to archive/realpage/
