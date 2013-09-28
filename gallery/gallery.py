import os

from docutils import nodes
from docutils.parsers.rst import directives, Directive

from pelican import signals


generator = None

DEFAULT_GALLERY_SETTINGS = {
}

class GalleryRst(Directive):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):
        template = generator.get_template('gallery')

        name = self.arguments[0]

        gallery = get_gallery(name)

        html = template.render(gallery=gallery)
        node = nodes.raw('', html, format='html')
        return [node]

def get_gallery(name, params={}):
    """
    Look for images in the gallery dir, process all images and create a
    gallery.

    :param String name: Name of the gallery
    :param Dict params: Additional parameters for the processing
    """
    settings = {}
    settings.update(DEFAULT_GALLERY_SETTINGS)
    settings.update(generator.settings.get('GALLERY_SETTINGS', {}))
    settings.update(params)

    contentpath = os.path.join(
        generator.settings.get('PATH'),
        'images/gallery'
    )

    images = {}

    gallerypath = os.path.join(contentpath, name)

    if not os.path.isdir(gallerypath):
        return None

    for n in os.listdir(gallerypath):
        if not os.path.isfile(os.path.join(gallerypath, n)):
            continue
        images[n] = {
            'filename': n,
        }

    return {
        'name': name,
        'images': images
    }


def generator_init(generator_obj):
    """
    We need a generator object to load templates and access the pelican
    settings.
    """
    global generator
    # there are multiple generators, but it's OK to use the first one
    if generator != None:
        return
    generator = generator_obj

def add_gallery_post(generator):

    contentpath = generator.settings.get('PATH')    
    gallerycontentpath = os.path.join(contentpath,'images/gallery')
    
    
    for article in generator.articles:
        if 'gallery' in article.metadata.keys():
            album = article.metadata.get('gallery')
            galleryimages = []
            
            articlegallerypath=os.path.join(gallerycontentpath, album)
            
            if(os.path.isdir(articlegallerypath)):       
                for i in os.listdir(articlegallerypath):
                    if os.path.isfile(os.path.join(os.path.join(gallerycontentpath, album), i)):
                        galleryimages.append(i)
        
            article.album=album
            article.galleryimages=galleryimages



def generate_gallery_page(generator):

    contentpath = generator.settings.get('PATH')    
    gallerycontentpath = os.path.join(contentpath,'images/gallery')
    
    
    for page in generator.pages:
        if page.metadata.get('template') == 'gallery':
            gallery=dict()
        
            for a in os.listdir(gallerycontentpath):
                if os.path.isdir(os.path.join(gallerycontentpath, a)):
                   
                    for i in os.listdir(os.path.join(gallerycontentpath, a)):
                        if os.path.isfile(os.path.join(os.path.join(gallerycontentpath, a), i)):
                            gallery.setdefault(a, []).append(i)
        
            page.gallery=gallery



def register():
    signals.article_generator_finalized.connect(add_gallery_post)
    signals.page_generator_finalized.connect(generate_gallery_page)
    signals.generator_init.connect(generator_init)
    directives.register_directive('gallery', GalleryRst)

