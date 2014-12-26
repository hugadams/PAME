from traits.api import Str, HasTraits, Instance, Button, implements, File, Property, Bool
from traitsui.api import View, Item, Group, Include
from interfaces import IMaterial, IAdapter
from os.path import basename

class BasicAdapter(HasTraits):
    """ Adapter for previewing, other things.  What is shown in "MATERIAL" tab. 
    populate_object() method used to show an instance of the material.
    """
    from basic_material import BasicMaterial
    implements(IAdapter)
    
    name=Str('Basic Material')
    source=Str('Abstract Base Class for material')
    notes=Str('Not Found')
    matobject = Instance(BasicMaterial)
    preview = Button

    def _preview_fired(self): 
        """ View the material as plot"""
        if self.matobject == None:
            self.populate_object()
        self.matobject.edit_traits(kind='livemodal')      #Modal screws up objects for some reason
        self.destory_object()

    def populate_object(self): 
        """Method used to instantiate an object to conserve resources"""
        self.matobject=self.BasicMaterial()

    def destory_object(self):
        """Method used to destroy an object; not sure if ever will be useful"""
        self.matobject=None

    basicgroup=Group(
        Item('name', style='readonly'),   #THESE ARENT READ ONLY!
        Item('source', style='readonly'),
        Item('notes'),
        Item('preview'), 
    )

    traitsview= View(Include('basicgroup'),              
                     resizable=True, width=400, height=200)


class ConstantAdapter(BasicAdapter):
    from material_models import Constant
    name="Constant"
    source="Custom Made"
    notes="Simply provide a constant value for the dielectric/index of refraction and it will return a constant array of values.  Can enter complex values in the form"
    matobject=Instance(Constant)

    def populate_object(self): 
        self.matobject=self.Constant()
        

class SellmeirAdapter(BasicAdapter):
    from material_models import Sellmeir
    name="Sellmeir dispersion for optical-fiber glass"
    source="Gupta Paper" #CITE
    matobject=Instance(Sellmeir)

    def populate_object(self): 
        self.matobject=self.Sellmeir()


class DrudeBulkAdapter(BasicAdapter):
    from material_models import DrudeBulk
    name="Drude Bulk"
    source="One of the gupta papers"
    notes="Uses lamplasma and lamcollision to predict dielectric function based on Drude model"
    matobject=Instance(DrudeBulk)

    def populate_object(self):
        self.matobject=self.DrudeBulk()

        
class NKJsonAdapter(BasicAdapter):
    """ Reads data from JSON database.  Json data must be of form:
    {dataset/filename : {
         x:xvals, n:nvals, k:kvals
         }
    With canonical form N = n + ik
    """
    


class ABCFileFileAdapter(BasicAdapter):
    from material_files import ABCFile
    source="N/A"
    notes="Basic File of unknown type"
    file_path = File
    matobject = Instance(ABCFile)
    name=Property(Str, depends_on='file_path')

    def populate_object(self): 
        self.matobject=self.ABCFile(file_path=self.file_path)

    def _get_name(self): 
        return 'Basic Object:  %s' % basename( self.file_path )
    
    def _set_name(self, newname): 
        self.name = newname


class SopraFileAdapter(ABCFileFileAdapter):
    from material_files import SopraFile
    
    source="Sopra file"
    notes="http://www.sspectra.com/sopra.html"

    def _get_name(self): 
        return basename(self.file_path)
    
    def populate_object(self): 
        self.matobject = self.SopraFile(file_path=self.file_path)
        

class XNKFileAdapter(ABCFileFileAdapter):
    from material_files import XNKFile, XNKFileCSV
    csv = Bool(False) 
    source="NK_Delimited File"
    notes="Assumes real and imaginary parts of the index of refraction in "\
    "delimited columns.  If header present, must be first line and begin with "\
    "a '#' character"

    def populate_object(self): 
        if self.csv:
            self.matobject = self.XNKFileCSV(file_path=self.file_path)            
        else:
            self.matobject = self.XNKFile(file_path=self.file_path)

    def _get_name(self): 
        return 'NK Delimited Object:  %s' % basename( self.file_path )




if __name__ == '__main__':
    BasicAdapter().configure_traits()
