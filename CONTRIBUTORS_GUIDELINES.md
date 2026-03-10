# Contributors Guidelines
Contributions could include research into improving or developing better 
methods, writing code, reviewing code, reviewing and updating manuals, etc. 
If your contributions involve writing code or updating manuals, please 
carefully review the guidelines described in this document. Adherence to 
these guidelines will facilitate efficient merging of your contributions 
into the project and keep the project style and documentation consistent.

## Code
All code and/or libraries used should be compatible with Python 3.13.11 and 
PyInstaller 6.17 or later and be licensed for free open-source use.

### General
It is important that the code be readable and well documented. [PEP8](https://www.python.org/dev/peps/pep-0008/) 
style should be followed as much as is practical. Since nearly all the 
code has been written using the Pycharm development environment and Pycharm 
defaults to a line length of 120 characters, QRevInt deviates for the PEP8 
recommendation of 79 character line length. From a development and 
readability perspective the 120 character length fits well on most monitors 
and enhances the readability of the code. However, a 79 character PEP8 
compatible line length is also acceptable. A good reference that covers 
common PEP8 coding style can be found at https://realpython.
com/python-pep8/. The use of a PEP8 linter or autoformatter such as Black or Ruff is encouraged.

### Organization
The code is stored in three folders: Classes, MiscLibs, and UI. The Classes 
folder contains the computational code for reading, processing, and storing 
data. MiscLibs contain various general computational modules that may be 
used in multiple Classes, such as, robust_loess.py or common_functions.py. 
The UI folder contains all the code for creating the user interface and 
responding to user input. For maintainability, it is important to **keep 
the user interface and the computational code separate.** The user 
interface methods should do minimal computations, such as only those 
required to create a plot. All other computations should be done in methods 
within the appropriate class. The computational classes should not contain 
code that creates any object displayed directly to the user (tables, graphs, etc.).

### Naming Conventions
All names should be descriptive. Avoid use of simple nondescriptive names 
such as a, b, c, etc., unless those are common abbreviations for the 
variable. Do not use a variable name that conflicts with a class attribute, 
such as, some_variable when the class has an attribute self.some_variable.

**Class** names should use CapWords or CamelCase convention.

**Function** names should be lowercase, with words separated by underscores 
as necessary to improve readability (this_example).

**Variable** names follow the same convention as function names.

### Documentation and Comments
Provide sufficient documentation and variable definitions so that someone 
else can understand the purpose and function of the code.

The [numpy docstring guide](https://numpydoc.readthedocs.io/en/latest/format.html#class-docstring)
 should be followed for documenting Classes and Methods. Simple examples are provided here:

```
class SomeClass(object):
    """This class provides an example of documentation for a class using numpy style docstrings.

    Attributes
    ----------
    top: float
        Transect total extrapolated top discharge
    top_ens: np.array(float)
        Extrapolated top discharge by ensemble
    left_idx: list
        Ensembles used for left edge
	gps: GPSData
        Object of GPSData
	checked: bool
        Setting for if transect was checked for use in mmt file assumed checked for SonTek
    in_transect_idx: np.array(int)
        Index of ensemble data associated with the moving-boat portion of the transect
    """

    def populate_from_qrev_mat(self, mat_data):
        """Populates the object using data from previously saved QRev Matlab file.

        Parameters
        ----------
        mat_data: mat_struct
           Matlab data structure obtained from sio.loadmat
        """
		
	@staticmethod
    def average_depth(depth, draft, method):
        """Compute average depth from bottom track beam depths.

        Parameters
        ----------
        depth: np.array(float)
            Individual beam depths for each beam in each ensemble including the draft
        draft: float
            Draft of ADCP
        method: str
            Averaging method (Simple, IDW)
        
        Returns
        -------
        avg_depth: np.array(float)
            Average depth for each ensemble
        
        """
```

Generally, comments should be provided on a separate line. Start the 
comment with # aligned with the code it is describing, followed by a space, 
and then the comment. For multi-line comments start each line with a # and 
space. Depending on the code, it is often helpful to precede the comment 
and code block with a blank line.
```
		# Compute draft change
        draft_change = draft - self.draft_use_m
        self.draft_use_m = draft
        
        # Apply draft to ensemble depths if BT or VB
        if self.depth_source != 'DS':
            self.depth_beams_m = self.depth_beams_m + draft_change
            self.depth_processed_m = self.depth_processed_m + draft_change 
```

Blank lines can be used without comments to separate blocks of code to 
improved readability.            

Use inline comments sparingly. If inline comments are used, write them on 
the same line as the statement they refer to. Separate inline comments by 
two or more spaces from the statement. Start inline comments with a # and a 
single space, like other comments.

### Other
Imports should be on separate lines. Wildcard imports ```(from <module> 
import *)``` should be avoided, as they make it unclear which names are 
present in the namespace, confusing both readers and many automated tools. 

Two blank lines between imports and class declaration.

One blank line between methods within a class.

Use ```@staticmethod``` decorator for methods that return a value rather 
than modify class attributes.

Be careful using the Python None as it must be explicitly trapped and 
changed before saving a file in Matlab format, as Matlab doesn't know how 
to interpret None.

## Manuals
Both the User's Manual and the Technical Manual must be kept up-to-date and 
accurately reflect the user interface and the computations. The title page 
of the manual should be dated, but should not include the version of the 
software. This allows updating the software (bug fixes) where no change in 
the manual(s) is necessary. Likewise, this allows the manual(s) to be 
updated without a new release of the software. The manuals are located in 
UI/Help. The manuals are prepared in Word and saved in both docx and pdf 
formats. The pdf format is included with the compiled releases and accessed 
through the in software help button. When making changes to the manuals 
please follow the formatting style used in the manual and check for proper 
pagination after making changes. 

The User's Manual begins with a figure that has hyperlinks to different 
sections of the manual. If the main GUI is changed the figure will have to 
be updated and any changes or additions to the hyperlinks made.

Both manuals have a table of contents that will need to be updated to 
reflect changes in the pagination as the manuals are modified. This can be 
a bit tricky at times so be careful and ask for help, if necessary.