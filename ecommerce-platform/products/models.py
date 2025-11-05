from django.db import models
# from django.utils import timezone
# Create your models here.

# multihierarchy catagory
class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    parent = models.ForeignKey('self',on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_leaf = models.BooleanField(default=False)

    class Meta:
        unique_together = (('parent', 'name'))
        ordering = ('name',)
    
    # Path node root to leaf
    def get_path(self):
        node = self
        path = []
        while node: # when parent becomes null
            path.append(node.name)
            node = node.parent
        return list(reversed(path))
    def __str__(self):
        return self.name
    
class Attribute(models.Model):
    # input choices for value of attribute
    INPUT_CHOICES = [
        ('text', 'Text'),
        ('int', 'Integer'),
        ('decimal', 'Decimal'),
        ('boolean', 'Boolean'),
    ]
    name = models.CharField(max_length=200)
    input_type = models.CharField(max_length=10, choices=INPUT_CHOICES, default='text')
    is_filterable = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='value')
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = (('attribute','value'),)
    
    def __str__(self):
        return f"{self.attribute.name} : {self.value}"

class CategoryAttribute(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE,related_name="category_attribute")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)

    class Meta:
        unique_together = (('category', 'attribute'),)
    
    def __str_(self):
        return f"{self.category} - {self.attribute}"

    
class Product(models.Model):
    status_choice = [
        ("active","Active"),("inactive", "Inactive"),("deleted","Deleted"),("pending","Pending"),
    ]
    # vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=status_choice,default='inactive')
    # stock = models.PositiveIntegerField(default=0)
    catagory = models.ManyToManyField(Category,related_name="products",blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True)
    adjusted_price = models.DecimalField(max_digits=10, decimal_places=2,null=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sku']
    
    def save(self, *args, **kwargs):
        if self.adjusted_price is None:
            self.adjusted_price = self.product.base_price
        super().save(*args,**kwargs)
  
    def __str__(self):
        return f"{self.product.title} - {self.sku}"

# class ProductImage(models.Model):
#     product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name="images")
#     is_primary = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.product.title} image"

class VariantAttribute(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(Attribute,on_delete=models.CASCADE)
    value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('variant', 'attribute'),)

    def __str__(self):
        return f"{self.variant.sku} - {self.attribute.name}: {self.value.value}"
    

class ProductVariantImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE,related_name='images')
    image = models.ImageField(upload_to='products')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary','created_at']
    
    def __str__(self):
        return f"Image for {self.product.title}"



