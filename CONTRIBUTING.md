Document initially started on May 25th, 2014, as written by Heufneutje. Update if necessary.

Here are some general guidelines when you're contributing to this project. This goes for all members, including the admins.

 - Always discuss major changes with the project's admins. These are HubbeKing, TyranicMoron and Heufneutje. Do this preferably by means of a GitHub issue.
 - While working on a big change, try using either a branch in a fork of this project, or in a separate branch in the main repository if you are a member.
 - Always test your code before committing anything. Make sure not only your own code works, but the integration of it into the rest of the project as well. When submitting a PR, Travis will automatically launch the bot with your changes to check that it still runs and can execute a few commands. Be sure to check the output from Travis if that fails.
 - When you commit something, use sane commit messages and squash your commits if needed. This way we can keep the commit history as clean as possible and we don't end up with a bunch of meaningless commits.

Secondly a proposal for the coding style. This is very open to suggestion, but for the sake of code readability and management, a good idea to keep in mind. Update these in agreement if necessary.

 - Indent using 4 spaces. You can configure your IDE to convert tabs to do this for you.
 - In general code should have a maximum line length of 120 characters, however sometimes this only serves to make the code less readable. Use your best judgement.
 - Always end files with a newline. Some editors will have this behaviour by default, but mostly on Windows you're going to have to pay attention to this.
 - Naming conventions:
   - Python file names should be all_lowercase
   - Class names should follow CapitalizedWords
   - Function and method names should follow mixedCase
   - Variables should also follow mixedCase
   - Constants should follow UPPER_CASE_WITH_UNDERSCORES
   - 'internal use' should be denoted with a _singleLeadingUnderscore
