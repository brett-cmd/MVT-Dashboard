# MVT-Dashboard Changelog

## Recent Fix - Check IOCs Functionality

### Issue
The "Check IOCs" button was not working properly:
- Output was only partially displayed
- No actual analysis was being performed
- The command `mvt-ios check-iocs` only checks existing JSON results against IOCs, not performing a full backup analysis

### Solution
1. **Changed the Check IOCs functionality** to run a full backup check with IOC checking enabled:
   - iOS: Now runs `mvt-ios check-backup` instead of `mvt-ios check-iocs`
   - Android: Now runs `mvt-android check-backup` instead of `mvt-android check-iocs`

2. **Updated button labels** to be clearer:
   - Changed from "Check IOCs" to "Check Backup with IOCs"
   - Updated tooltips to explain it runs a full backup analysis with IOC checking

3. **Improved CommandRunner** output handling:
   - Added better error handling to continue reading output even if there are temporary read errors
   - Added stdout flush to ensure all output is captured
   - Fixed output line tracking for both process output scenarios

### Technical Details
- The `check-iocs` command in MVT only checks already extracted JSON results against IOCs
- To perform a full analysis with IOC checking (like the CLI example), you need to run `check-backup` 
- MVT automatically loads and uses IOCs during backup checks if they are downloaded

### Result
Now when you click "Check Backup with IOCs", it will:
1. Run a full backup analysis on the selected path
2. Automatically check against downloaded IOCs during the analysis
3. Generate complete output and result files
4. Display all output in the console properly 