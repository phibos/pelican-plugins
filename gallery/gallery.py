import os
import logging
logger = logging.getLogger(__name__)

from docutils import nodes
from docutils.parsers.rst import directives, Directive

from pelican import signals, utils

try:
    from PIL import Image, ImageOps
except ImportError:
    logging.warning("Unable to load PIL")

generator = None

DEFAULT_GALLERY_SETTINGS = {
    'content_path': 'gallery',
    'copy_original': True,
    'output_path': 'images/gallery',
    'sizes': {},
    'template_embedded': 'gallery-embedded',
    'thumbnail_create': False,
    'thumbnail_mode': 'fit',
    'thumbnail_path': 'thumbs',
    'thumbnail_size': 150,
}

class GalleryRst(Directive):
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = True

    def run(self):

        name = self.arguments[0]

        settings = prepare_settings()
        gallery = get_gallery(name)

        template = generator.get_template(settings.get('template_embedded'))

        html = template.render(gallery=gallery)
        node = nodes.raw('', html, format='html')
        return [node]

def prepare_settings(params={}):
    """
    Combine default and user settings and return the result as dict.

    :param Dict params: Additional parameters to combine
    """
    settings = {}
    settings.update(DEFAULT_GALLERY_SETTINGS)
    settings.update(generator.settings.get('GALLERY_SETTINGS', {}))
    settings.update(params)
    return settings

def get_gallery(name, params={}):
    """
    Look for images in the gallery dir, process all images and create a
    gallery.

    :param String name: Name of the gallery
    :param Dict params: Additional parameters for the processing
    """
    settings = prepare_settings(params)

    # check content path
    content_path = os.path.join(
        generator.settings.get('PATH'),
        settings.get('content_path')
    )
    gallery_content_path = os.path.join(content_path, name)

    if not os.path.isdir(gallery_content_path):
        logging.warning("Unable to find gallery: %s", name)
        return None

    # prepare output directories
    output_path = os.path.join(
        generator.settings.get('OUTPUT_PATH'),
        settings.get('output_path'),
        name
    )
    thumbnail_path = os.path.join(
        output_path,
        settings.get('thumbnail_path')
    )

    # create directories
    utils.mkdir_p(output_path)
    if settings.get('thumbnail_create') == True:
        utils.mkdir_p(thumbnail_path)

    # process the images
    images = {}
    for filename in os.listdir(gallery_content_path):
        if not os.path.isfile(os.path.join(gallery_content_path, filename)):
            continue

        image = {}
        # copy original
        if settings.get('copy_original') == True:
            utils.copy(filename, gallery_content_path, output_path, './')
            image['filename'] = filename

        # load the image
        img = Image.open(os.path.join(gallery_content_path, filename))
        # process the thumbnail
        if settings.get('thumbnail_create') == True:
            size = settings.get('thumbnail_size')
            if type(size) == int:
                size = (size, size)

            mode = settings.get('thumbnail_mode')
            if mode == 'fit':
                img_new = ImageOps.fit(img, size)
            else:
                img_new = ImageOps.fit(img, size)

            img_new.save(os.path.join(thumbnail_path, filename))
            image['thumbnail'] = settings.get('thumbnail_path') + '/' + filename

        # process the image sizes
        img_sizes = {}
        for sname, sopt in settings.get('sizes').iteritems():
            size = sopt.get('size')
            if type(size) == int:
                size = (size, size)
            x, y = img.size
            if x > size[0]: y = int(max(y * size[0] / x, 1)); x = int(size[0])
            if y > size[1]: x = int(max(x * size[1] / y, 1)); y = int(size[1])
            size = (x, y)
            img_new = img.resize(size)
            img_name = sopt.get('name', '{root}_{size_name}.{ext}').format(
                root=os.path.splitext(filename)[0],
                ext=os.path.splitext(filename)[1][1:],
                size_name=sname
            )

            img_new.save(
                os.path.join(
                    output_path,
                    img_name
                )
            )
            img_sizes[sname] = img_name

        image['sizes'] = img_sizes


        images[filename] = image

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

