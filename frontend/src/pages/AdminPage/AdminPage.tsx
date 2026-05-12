import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { adminCatalogApi } from "@features/adminCatalog/api/adminCatalogApi";
import { isApiError } from "@shared/api";
import type { CategoryRead, DecimalString, ProductCreate, ProductRead, ProductUnit } from "@shared/api";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, Modal, PageHeader, SelectField, TextField, useToast } from "@shared/ui";
import { AdminLoginAuditPanel } from "./AdminLoginAuditPanel";
import { AdminOrdersPanel } from "./AdminOrdersPanel";
import { AdminUsersPanel } from "./AdminUsersPanel";
import "./AdminPage.css";

const PRODUCT_UNITS: Array<{ label: string; value: ProductUnit }> = [
  { label: "шт", value: "шт" },
  { label: "кг", value: "кг" },
  { label: "г", value: "г" },
  { label: "л", value: "л" },
  { label: "мл", value: "мл" },
  { label: "уп", value: "уп" },
];

const DEFAULT_UNIT = PRODUCT_UNITS[0].value;
const IMAGE_ID_PATTERN = /^[a-fA-F0-9]{24}$/;

type AdminTab = "audit" | "categories" | "orders" | "products" | "users";
type CategoryModalMode = "create" | "edit";
type ProductModalMode = "create" | "edit";
type ProductStatusFilter = "active" | "all" | "inactive";

type CategoryFormState = {
  id: string;
  name: string;
  slug: string;
};

type ProductFormState = {
  brand: string;
  categoryId: string;
  description: string;
  isActive: boolean;
  name: string;
  photoIdInput: string;
  photoIds: string[];
  price: string;
  sku: string;
  stock: string;
  unit: ProductUnit;
};

const emptyCategoryForm: CategoryFormState = {
  id: "",
  name: "",
  slug: "",
};

function createProductForm(categoryId = ""): ProductFormState {
  return {
    brand: "",
    categoryId,
    description: "",
    isActive: true,
    name: "",
    photoIdInput: "",
    photoIds: [],
    price: "",
    sku: "",
    stock: "0",
    unit: DEFAULT_UNIT,
  };
}

function productToForm(product: ProductRead): ProductFormState {
  return {
    brand: product.brand ?? "",
    categoryId: String(product.category_id),
    description: product.description,
    isActive: product.is_active,
    name: product.name,
    photoIdInput: "",
    photoIds: product.photo_ids,
    price: String(product.price),
    sku: product.sku,
    stock: String(product.stock),
    unit: product.unit,
  };
}

function getErrorMessage(error: unknown) {
  if (isApiError(error)) {
    return error.detail;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Catalog request failed.";
}

function formatPrice(value: DecimalString) {
  const numberValue = Number(value);

  if (!Number.isFinite(numberValue)) {
    return String(value);
  }

  return new Intl.NumberFormat("ru-RU", {
    currency: "RUB",
    maximumFractionDigits: 2,
    style: "currency",
  }).format(numberValue);
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getImageUrl(photoId: string) {
  return `/api/images/${photoId}`;
}

function appendUnique(values: string[], value: string) {
  return values.includes(value) ? values : [...values, value];
}

function getNextCategoryId(categories: CategoryRead[]) {
  return String(Math.max(0, ...categories.map((category) => category.id)) + 1);
}

function slugify(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function AdminPage() {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<AdminTab>("products");
  const [categories, setCategories] = useState<CategoryRead[]>([]);
  const [categoryForm, setCategoryForm] = useState<CategoryFormState>(emptyCategoryForm);
  const [categoryModalMode, setCategoryModalMode] = useState<CategoryModalMode | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mutation, setMutation] = useState<string | null>(null);
  const [productForm, setProductForm] = useState<ProductFormState>(() => createProductForm());
  const [productModalMode, setProductModalMode] = useState<ProductModalMode | null>(null);
  const [products, setProducts] = useState<ProductRead[]>([]);
  const [query, setQuery] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [selectedCategory, setSelectedCategory] = useState<CategoryRead | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<ProductRead | null>(null);
  const [statusFilter, setStatusFilter] = useState<ProductStatusFilter>("all");

  useEffect(() => {
    const controller = new AbortController();

    setIsLoading(true);
    setError(null);
    Promise.all([
      adminCatalogApi.listCategories({ signal: controller.signal }),
      adminCatalogApi.listProducts({ active_only: false, limit: 100, offset: 0 }, { signal: controller.signal }),
    ])
      .then(([categoryPayload, productPayload]) => {
        if (controller.signal.aborted) {
          return;
        }

        setCategories(categoryPayload);
        setProducts(productPayload);
      })
      .catch((caughtError) => {
        if (!controller.signal.aborted) {
          setError(getErrorMessage(caughtError));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });

    return () => controller.abort();
  }, [reloadKey]);

  const categoryMap = useMemo(
    () => new Map(categories.map((category) => [category.id, category])),
    [categories],
  );

  const categoryOptions = useMemo(
    () => [
      { label: "All categories", value: "" },
      ...categories.map((category) => ({
        label: category.name,
        value: String(category.id),
      })),
    ],
    [categories],
  );

  const productCategoryOptions = useMemo(
    () => [
      { label: "Choose category", value: "" },
      ...categories.map((category) => ({
        label: category.name,
        value: String(category.id),
      })),
    ],
    [categories],
  );

  const filteredProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return products.filter((product) => {
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && product.is_active) ||
        (statusFilter === "inactive" && !product.is_active);
      const matchesCategory = !categoryFilter || String(product.category_id) === categoryFilter;
      const matchesQuery =
        !normalizedQuery ||
        [product.name, product.sku, product.brand ?? "", product.description]
          .join(" ")
          .toLowerCase()
          .includes(normalizedQuery);

      return matchesStatus && matchesCategory && matchesQuery;
    });
  }, [categoryFilter, products, query, statusFilter]);

  const summary = useMemo(
    () => ({
      activeProducts: products.filter((product) => product.is_active).length,
      categories: categories.length,
      lowStock: products.filter((product) => product.stock <= 5).length,
      totalProducts: products.length,
    }),
    [categories.length, products],
  );

  const refreshCatalog = () => setReloadKey((current) => current + 1);

  const openCreateCategory = () => {
    setSelectedCategory(null);
    setCategoryForm({
      ...emptyCategoryForm,
      id: getNextCategoryId(categories),
    });
    setCategoryModalMode("create");
  };

  const openEditCategory = (category: CategoryRead) => {
    setSelectedCategory(category);
    setCategoryForm({
      id: String(category.id),
      name: category.name,
      slug: category.slug,
    });
    setCategoryModalMode("edit");
  };

  const closeCategoryModal = () => {
    setCategoryModalMode(null);
    setSelectedCategory(null);
    setCategoryForm(emptyCategoryForm);
  };

  const openCreateProduct = () => {
    setSelectedProduct(null);
    setProductForm(createProductForm(categories[0] ? String(categories[0].id) : ""));
    setProductModalMode("create");
  };

  const openEditProduct = (product: ProductRead) => {
    setSelectedProduct(product);
    setProductForm(productToForm(product));
    setProductModalMode("edit");
  };

  const closeProductModal = () => {
    setProductModalMode(null);
    setSelectedProduct(null);
    setProductForm(createProductForm());
  };

  const handleCategoryNameChange = (value: string) => {
    setCategoryForm((current) => ({
      ...current,
      name: value,
      slug: current.slug || slugify(value),
    }));
  };

  const handleSaveCategory = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const categoryId = Number(categoryForm.id);
    if (!Number.isInteger(categoryId) || categoryId < 1) {
      showToast({ title: "Category ID is invalid", variant: "error" });
      return;
    }

    setMutation("category-save");
    setError(null);

    try {
      if (categoryModalMode === "create") {
        await adminCatalogApi.createCategory({
          id: categoryId,
          name: categoryForm.name.trim(),
          slug: categoryForm.slug.trim(),
        });
      } else if (selectedCategory) {
        await adminCatalogApi.updateCategory(selectedCategory.id, {
          name: categoryForm.name.trim(),
          slug: categoryForm.slug.trim(),
        });
      }

      showToast({ title: "Category saved", variant: "success" });
      closeCategoryModal();
      refreshCatalog();
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Category save failed",
        variant: "error",
      });
    } finally {
      setMutation(null);
    }
  };

  const handleDeleteCategory = async (category: CategoryRead) => {
    if (!window.confirm(`Delete category "${category.name}"?`)) {
      return;
    }

    setMutation(`category-delete:${category.id}`);
    setError(null);

    try {
      await adminCatalogApi.deleteCategory(category.id);
      setCategories((current) => current.filter((item) => item.id !== category.id));
      showToast({ title: "Category deleted", variant: "success" });
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Category delete failed",
        variant: "error",
      });
    } finally {
      setMutation(null);
    }
  };

  const buildProductPayload = (): ProductCreate | null => {
    const categoryId = Number(productForm.categoryId);
    const price = Number(productForm.price);
    const stock = Number(productForm.stock);

    if (!Number.isInteger(categoryId) || categoryId < 1) {
      showToast({ title: "Choose a category", variant: "error" });
      return null;
    }

    if (!Number.isFinite(price) || price < 0) {
      showToast({ title: "Price is invalid", variant: "error" });
      return null;
    }

    if (!Number.isInteger(stock) || stock < 0) {
      showToast({ title: "Stock is invalid", variant: "error" });
      return null;
    }

    return {
      brand: productForm.brand.trim() || null,
      category_id: categoryId,
      description: productForm.description.trim(),
      is_active: productForm.isActive,
      name: productForm.name.trim(),
      photo_ids: productForm.photoIds,
      price,
      sku: productForm.sku.trim().toUpperCase(),
      stock,
      unit: productForm.unit,
    };
  };

  const handleSaveProduct = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const payload = buildProductPayload();
    if (!payload) {
      return;
    }

    setMutation("product-save");
    setError(null);

    try {
      if (productModalMode === "create") {
        await adminCatalogApi.createProduct(payload);
      } else if (selectedProduct) {
        await adminCatalogApi.updateProduct(selectedProduct.id, payload);
      }

      showToast({ title: "Product saved", variant: "success" });
      closeProductModal();
      refreshCatalog();
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Product save failed",
        variant: "error",
      });
    } finally {
      setMutation(null);
    }
  };

  const handleDeleteProduct = async (product: ProductRead) => {
    if (!window.confirm(`Delete product "${product.name}"?`)) {
      return;
    }

    setMutation(`product-delete:${product.id}`);
    setError(null);

    try {
      await adminCatalogApi.deleteProduct(product.id);
      setProducts((current) => current.filter((item) => item.id !== product.id));
      showToast({ title: "Product deleted", variant: "success" });
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Product delete failed",
        variant: "error",
      });
    } finally {
      setMutation(null);
    }
  };

  const handleUploadPhoto = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) {
      return;
    }

    setMutation("image-upload");

    try {
      const image = await adminCatalogApi.uploadImage(file);
      setProductForm((current) => ({
        ...current,
        photoIds: appendUnique(current.photoIds, image.id),
      }));
      showToast({
        description: image.filename,
        title: "Image uploaded",
        variant: "success",
      });
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Image upload failed",
        variant: "error",
      });
    } finally {
      setMutation(null);
    }
  };

  const handleAttachPhotoId = () => {
    const photoId = productForm.photoIdInput.trim();

    if (!IMAGE_ID_PATTERN.test(photoId)) {
      showToast({
        description: "Use a 24-character Mongo ObjectId.",
        title: "Photo ID is invalid",
        variant: "error",
      });
      return;
    }

    setProductForm((current) => ({
      ...current,
      photoIdInput: "",
      photoIds: appendUnique(current.photoIds, photoId),
    }));
  };

  const handleUnlinkPhoto = (photoId: string) => {
    setProductForm((current) => ({
      ...current,
      photoIds: current.photoIds.filter((item) => item !== photoId),
    }));
  };

  const handleDeletePhotoFile = async (photoId: string) => {
    if (!window.confirm("Delete this image file from storage?")) {
      return;
    }

    setMutation(`image-delete:${photoId}`);

    try {
      await adminCatalogApi.deleteImage(photoId);
      setProductForm((current) => ({
        ...current,
        photoIds: current.photoIds.filter((item) => item !== photoId),
      }));
      showToast({ title: "Image deleted", variant: "success" });
      refreshCatalog();
    } catch (caughtError) {
      showToast({
        description: getErrorMessage(caughtError),
        title: "Image delete failed",
        variant: "error",
      });
    } finally {
      setMutation(null);
    }
  };

  const isCatalogTab = activeTab === "products" || activeTab === "categories";
  const pageCopy = {
    audit: {
      description: "Review login attempts by user, email, result, event type, IP address, and time range.",
      title: "Login audit",
    },
    categories: {
      description: "Catalog operations for categories, products, product photos, inventory, and publication status.",
      title: "Catalog",
    },
    orders: {
      description: "Manage order lifecycle statuses, admin cancellations, payments, deliveries, and status history.",
      title: "Orders",
    },
    products: {
      description: "Catalog operations for categories, products, product photos, inventory, and publication status.",
      title: "Catalog",
    },
    users: {
      description: "Manage user roles, active state, blocks, and email verification.",
      title: "Users",
    },
  } satisfies Record<AdminTab, { description: string; title: string }>;

  return (
    <div className="admin-page page-stack">
      <PageHeader
        actions={
          isCatalogTab ? (
            <div className="admin-header-actions">
              <Button onClick={refreshCatalog} variant="secondary">
                Refresh
              </Button>
              <Button onClick={openCreateCategory} variant="secondary">
                New category
              </Button>
              <Button disabled={!categories.length} onClick={openCreateProduct}>
                New product
              </Button>
            </div>
          ) : undefined
        }
        description={pageCopy[activeTab].description}
        eyebrow="Admin"
        title={pageCopy[activeTab].title}
      />

      {isCatalogTab ? (
        <section className="admin-summary" aria-label="Catalog summary">
          <article className="surface-card">
            <span>Products</span>
            <strong>{summary.totalProducts}</strong>
          </article>
          <article className="surface-card">
            <span>Active</span>
            <strong>{summary.activeProducts}</strong>
          </article>
          <article className="surface-card">
            <span>Low stock</span>
            <strong>{summary.lowStock}</strong>
          </article>
          <article className="surface-card">
            <span>Categories</span>
            <strong>{summary.categories}</strong>
          </article>
        </section>
      ) : null}

      <div className="admin-tabs" role="tablist" aria-label="Admin sections">
        <button
          aria-selected={activeTab === "products"}
          className={activeTab === "products" ? "is-active" : undefined}
          onClick={() => setActiveTab("products")}
          role="tab"
          type="button"
        >
          Products
        </button>
        <button
          aria-selected={activeTab === "categories"}
          className={activeTab === "categories" ? "is-active" : undefined}
          onClick={() => setActiveTab("categories")}
          role="tab"
          type="button"
        >
          Categories
        </button>
        <button
          aria-selected={activeTab === "orders"}
          className={activeTab === "orders" ? "is-active" : undefined}
          onClick={() => setActiveTab("orders")}
          role="tab"
          type="button"
        >
          Orders
        </button>
        <button
          aria-selected={activeTab === "users"}
          className={activeTab === "users" ? "is-active" : undefined}
          onClick={() => setActiveTab("users")}
          role="tab"
          type="button"
        >
          Users
        </button>
        <button
          aria-selected={activeTab === "audit"}
          className={activeTab === "audit" ? "is-active" : undefined}
          onClick={() => setActiveTab("audit")}
          role="tab"
          type="button"
        >
          Login audit
        </button>
      </div>

      {isCatalogTab && error ? (
        <ErrorState
          action={
            <Button onClick={refreshCatalog} variant="secondary">
              Retry
            </Button>
          }
          description={error}
          title="Unable to load catalog"
        />
      ) : null}

      {activeTab === "orders" ? (
        <AdminOrdersPanel />
      ) : activeTab === "users" ? (
        <AdminUsersPanel />
      ) : activeTab === "audit" ? (
        <AdminLoginAuditPanel />
      ) : isLoading ? (
        <LoadingState description="Loading categories and products." title="Loading catalog" />
      ) : activeTab === "products" ? (
        <section className="admin-panel" aria-label="Product management">
          <div className="admin-toolbar">
            <TextField
              label="Search"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Name, SKU, brand"
              value={query}
            />
            <SelectField
              label="Status"
              onChange={(event) => setStatusFilter(event.target.value as ProductStatusFilter)}
              options={[
                { label: "All statuses", value: "all" },
                { label: "Active", value: "active" },
                { label: "Inactive", value: "inactive" },
              ]}
              value={statusFilter}
            />
            <SelectField
              label="Category"
              onChange={(event) => setCategoryFilter(event.target.value)}
              options={categoryOptions}
              value={categoryFilter}
            />
          </div>

          <DataTable
            columns={[
              {
                key: "product",
                title: "Product",
                render: (product) => (
                  <div className="admin-product-cell">
                    <div className="admin-thumb">
                      {product.primary_photo_url ? (
                        <img alt={product.name} src={product.primary_photo_url} />
                      ) : (
                        <span>{product.name.slice(0, 1).toUpperCase()}</span>
                      )}
                    </div>
                    <div>
                      <strong>{product.name}</strong>
                      <span>{product.sku}</span>
                    </div>
                  </div>
                ),
              },
              {
                key: "category",
                title: "Category",
                render: (product) => categoryMap.get(product.category_id)?.name ?? `Category ${product.category_id}`,
              },
              {
                align: "right",
                key: "price",
                title: "Price",
                render: (product) => formatPrice(product.price),
              },
              {
                align: "right",
                key: "stock",
                title: "Stock",
                render: (product) => (
                  <span className={product.stock <= 5 ? "admin-badge is-warning" : "admin-badge"}>
                    {product.stock}
                  </span>
                ),
              },
              {
                key: "status",
                title: "Status",
                render: (product) => (
                  <span className={product.is_active ? "admin-badge is-success" : "admin-badge is-muted"}>
                    {product.is_active ? "Active" : "Inactive"}
                  </span>
                ),
              },
              {
                key: "photos",
                title: "Photos",
                render: (product) => (
                  <div className="admin-photo-strip">
                    {product.photo_ids.slice(0, 3).map((photoId) => (
                      <img alt="" key={photoId} src={getImageUrl(photoId)} />
                    ))}
                    <span>{product.photo_ids.length}</span>
                  </div>
                ),
              },
              {
                align: "right",
                key: "actions",
                title: "Actions",
                render: (product) => (
                  <div className="admin-row-actions">
                    <Button onClick={() => openEditProduct(product)} size="sm" variant="secondary">
                      Edit
                    </Button>
                    <Button
                      isLoading={mutation === `product-delete:${product.id}`}
                      onClick={() => void handleDeleteProduct(product)}
                      size="sm"
                      variant="danger"
                    >
                      Delete
                    </Button>
                  </div>
                ),
              },
            ]}
            empty={
              <EmptyState
                action={
                  <Button disabled={!categories.length} onClick={openCreateProduct}>
                    New product
                  </Button>
                }
                description="No products match the current filters."
                title="No products"
              />
            }
            getRowKey={(product) => product.id}
            rows={filteredProducts}
          />
        </section>
      ) : (
        <section className="admin-panel" aria-label="Category management">
          <DataTable
            columns={[
              { key: "id", title: "ID", render: (category) => category.id },
              { key: "name", title: "Name", render: (category) => category.name },
              { key: "slug", title: "Slug", render: (category) => <code>{category.slug}</code> },
              { key: "updated", title: "Updated", render: (category) => formatDate(category.updated_at) },
              {
                align: "right",
                key: "actions",
                title: "Actions",
                render: (category) => (
                  <div className="admin-row-actions">
                    <Button onClick={() => openEditCategory(category)} size="sm" variant="secondary">
                      Edit
                    </Button>
                    <Button
                      isLoading={mutation === `category-delete:${category.id}`}
                      onClick={() => void handleDeleteCategory(category)}
                      size="sm"
                      variant="danger"
                    >
                      Delete
                    </Button>
                  </div>
                ),
              },
            ]}
            empty={
              <EmptyState
                action={<Button onClick={openCreateCategory}>New category</Button>}
                description="Create a category before adding products."
                title="No categories"
              />
            }
            getRowKey={(category) => String(category.id)}
            rows={categories}
          />
        </section>
      )}

      <Modal
        footer={
          <>
            <Button onClick={closeCategoryModal} variant="secondary">
              Cancel
            </Button>
            <Button form="category-form" isLoading={mutation === "category-save"} type="submit">
              Save
            </Button>
          </>
        }
        isOpen={Boolean(categoryModalMode)}
        onClose={closeCategoryModal}
        title={categoryModalMode === "edit" ? "Edit category" : "New category"}
      >
        <form className="admin-form" id="category-form" onSubmit={handleSaveCategory}>
          <TextField
            disabled={categoryModalMode === "edit"}
            label="ID"
            min="1"
            onChange={(event) => setCategoryForm((current) => ({ ...current, id: event.target.value }))}
            required
            type="number"
            value={categoryForm.id}
          />
          <TextField
            label="Name"
            maxLength={100}
            minLength={2}
            onChange={(event) => handleCategoryNameChange(event.target.value)}
            required
            value={categoryForm.name}
          />
          <TextField
            label="Slug"
            maxLength={100}
            minLength={2}
            onChange={(event) => setCategoryForm((current) => ({ ...current, slug: event.target.value }))}
            pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$"
            required
            value={categoryForm.slug}
          />
        </form>
      </Modal>

      <Modal
        footer={
          <>
            <Button onClick={closeProductModal} variant="secondary">
              Cancel
            </Button>
            <Button disabled={!categories.length} form="product-form" isLoading={mutation === "product-save"} type="submit">
              Save
            </Button>
          </>
        }
        isOpen={Boolean(productModalMode)}
        onClose={closeProductModal}
        title={productModalMode === "edit" ? "Edit product" : "New product"}
      >
        <form className="admin-form admin-product-form" id="product-form" onSubmit={handleSaveProduct}>
          <div className="admin-form-grid">
            <TextField
              label="SKU"
              maxLength={64}
              minLength={3}
              onChange={(event) => setProductForm((current) => ({ ...current, sku: event.target.value }))}
              pattern="^[A-Za-z0-9_-]{3,64}$"
              required
              value={productForm.sku}
            />
            <TextField
              label="Name"
              maxLength={120}
              minLength={2}
              onChange={(event) => setProductForm((current) => ({ ...current, name: event.target.value }))}
              required
              value={productForm.name}
            />
            <TextField
              label="Brand"
              maxLength={120}
              minLength={2}
              onChange={(event) => setProductForm((current) => ({ ...current, brand: event.target.value }))}
              value={productForm.brand}
            />
            <SelectField
              label="Category"
              onChange={(event) => setProductForm((current) => ({ ...current, categoryId: event.target.value }))}
              options={productCategoryOptions}
              required
              value={productForm.categoryId}
            />
            <TextField
              inputMode="decimal"
              label="Price"
              min="0"
              onChange={(event) => setProductForm((current) => ({ ...current, price: event.target.value }))}
              required
              step="0.01"
              type="number"
              value={productForm.price}
            />
            <SelectField
              label="Unit"
              onChange={(event) => setProductForm((current) => ({ ...current, unit: event.target.value as ProductUnit }))}
              options={PRODUCT_UNITS}
              value={productForm.unit}
            />
            <TextField
              label="Stock"
              min="0"
              onChange={(event) => setProductForm((current) => ({ ...current, stock: event.target.value }))}
              required
              step="1"
              type="number"
              value={productForm.stock}
            />
            <label className="admin-checkbox">
              <input
                checked={productForm.isActive}
                onChange={(event) => setProductForm((current) => ({ ...current, isActive: event.target.checked }))}
                type="checkbox"
              />
              <span>Active product</span>
            </label>
          </div>

          <label className="ds-field" htmlFor="admin-product-description">
            <span className="ds-field__label">Description</span>
            <textarea
              className="ds-input admin-textarea"
              id="admin-product-description"
              maxLength={2000}
              minLength={10}
              onChange={(event) => setProductForm((current) => ({ ...current, description: event.target.value }))}
              required
              value={productForm.description}
            />
          </label>

          <section className="admin-image-editor" aria-label="Product images">
            <div className="admin-image-tools">
              <label className={mutation === "image-upload" ? "admin-upload is-disabled" : "admin-upload"}>
                <span>{mutation === "image-upload" ? "Uploading..." : "Upload image"}</span>
                <input
                  accept="image/gif,image/jpeg,image/png,image/webp"
                  disabled={mutation === "image-upload"}
                  onChange={handleUploadPhoto}
                  type="file"
                />
              </label>
              <div className="admin-photo-input-row">
                <TextField
                  label="Photo ID"
                  onChange={(event) => setProductForm((current) => ({ ...current, photoIdInput: event.target.value }))}
                  placeholder="6622eacaf2f4b22a4eb8ac11"
                  value={productForm.photoIdInput}
                />
                <Button onClick={handleAttachPhotoId} variant="secondary">
                  Attach
                </Button>
              </div>
            </div>

            {productForm.photoIds.length ? (
              <div className="admin-photo-list">
                {productForm.photoIds.map((photoId) => (
                  <article className="admin-photo-item" key={photoId}>
                    <img alt="" src={getImageUrl(photoId)} />
                    <code>{photoId}</code>
                    <div>
                      <Button onClick={() => handleUnlinkPhoto(photoId)} size="sm" variant="secondary">
                        Unlink
                      </Button>
                      <Button
                        isLoading={mutation === `image-delete:${photoId}`}
                        onClick={() => void handleDeletePhotoFile(photoId)}
                        size="sm"
                        variant="danger"
                      >
                        Delete file
                      </Button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <EmptyState description="Upload an image or attach an existing photo ID." title="No product images" />
            )}
          </section>
        </form>
      </Modal>
    </div>
  );
}
