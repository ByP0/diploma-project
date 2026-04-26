import type {
  CheckoutFieldErrors,
  CheckoutFormState,
  CheckoutPayload,
  CheckoutStepId,
  DeliveryWindowOption,
} from "./checkout.types";

const phonePattern = /^[0-9+()\-\s]+$/;

export function validateCheckoutStep(
  step: CheckoutStepId,
  form: CheckoutFormState,
  windows: DeliveryWindowOption[],
): CheckoutFieldErrors {
  const errors: CheckoutFieldErrors = {};

  if (step === "items") {
    return errors;
  }

  if (step === "address") {
    validateCustomer(errors, form);
  }

  if (step === "delivery") {
    validateDelivery(errors, form, windows);
  }

  if (step === "payment") {
    validatePayment(errors, form);
  }

  if (step === "summary") {
    validateCustomer(errors, form);
    if (form.deliveryMethod !== "pickup") {
      validateAddress(errors, form);
    }
    validateDelivery(errors, form, windows);
    validatePayment(errors, form);
  }

  return errors;
}

export function validateCheckoutForm(form: CheckoutFormState, windows: DeliveryWindowOption[]) {
  return validateCheckoutStep("summary", form, windows);
}

export function hasCheckoutErrors(errors: CheckoutFieldErrors) {
  return Object.keys(errors).length > 0;
}

export function getFirstInvalidStep(errors: CheckoutFieldErrors): CheckoutStepId {
  if (errors.cart) {
    return "items";
  }

  if (
    errors.customerName ||
    errors.customerPhone ||
    errors.deliveryAddressLine1 ||
    errors.deliveryCity ||
    errors.deliveryCountry
  ) {
    return "address";
  }

  if (errors.deliveryWindowId) {
    return "delivery";
  }

  if (errors.paymentMethod || errors.paymentProvider) {
    return "payment";
  }

  return "summary";
}

export function buildCheckoutPayload(
  form: CheckoutFormState,
  windows: DeliveryWindowOption[],
): CheckoutPayload {
  const deliveryWindow = windows.find((windowOption) => windowOption.id === form.deliveryWindowId) ?? windows[0];
  const isPickup = form.deliveryMethod === "pickup";

  return {
    customer_name: form.customerName.trim(),
    customer_phone: form.customerPhone.trim(),
    customer_comment: optionalString(form.customerComment),
    delivery_method: form.deliveryMethod,
    payment_method: form.paymentMethod,
    payment_provider: form.paymentMethod === "card_online" ? form.paymentProvider : null,
    delivery_window_start: deliveryWindow?.start ?? null,
    delivery_window_end: deliveryWindow?.end ?? null,
    delivery_address_line1: isPickup ? null : optionalString(form.deliveryAddressLine1),
    delivery_address_line2: isPickup ? null : optionalString(form.deliveryAddressLine2),
    delivery_city: isPickup ? null : optionalString(form.deliveryCity),
    delivery_region: isPickup ? null : optionalString(form.deliveryRegion),
    delivery_postal_code: isPickup ? null : optionalString(form.deliveryPostalCode),
    delivery_country: form.deliveryCountry.trim().toUpperCase() || "RU",
    delivery_floor: isPickup ? null : optionalString(form.deliveryFloor),
    delivery_apartment: isPickup ? null : optionalString(form.deliveryApartment),
    delivery_entrance: isPickup ? null : optionalString(form.deliveryEntrance),
    delivery_intercom: isPickup ? null : optionalString(form.deliveryIntercom),
    delivery_instructions: optionalString(form.deliveryInstructions),
    currency: form.currency,
  };
}

function validateCustomer(errors: CheckoutFieldErrors, form: CheckoutFormState) {
  if (form.customerName.trim().length < 2) {
    errors.customerName = "Укажите имя получателя минимум из 2 символов.";
  }

  const phone = form.customerPhone.trim();
  if (phone.length < 7) {
    errors.customerPhone = "Укажите номер телефона для связи с курьером.";
  } else if (!phonePattern.test(phone)) {
    errors.customerPhone = "Телефон может содержать цифры, пробелы, +, скобки и дефисы.";
  }
}

function validateAddress(errors: CheckoutFieldErrors, form: CheckoutFormState) {
  if (!form.deliveryAddressLine1.trim()) {
    errors.deliveryAddressLine1 = "Укажите улицу, дом и корпус.";
  }

  if (!form.deliveryCity.trim()) {
    errors.deliveryCity = "Укажите город доставки.";
  }

  if (form.deliveryCountry.trim().length !== 2) {
    errors.deliveryCountry = "Код страны должен состоять из 2 букв.";
  }
}

function validateDelivery(
  errors: CheckoutFieldErrors,
  form: CheckoutFormState,
  windows: DeliveryWindowOption[],
) {
  if (!windows.some((windowOption) => windowOption.id === form.deliveryWindowId)) {
    errors.deliveryWindowId = "Выберите доступный интервал доставки.";
  }
}

function validatePayment(errors: CheckoutFieldErrors, form: CheckoutFormState) {
  if (!form.paymentMethod) {
    errors.paymentMethod = "Выберите способ оплаты.";
  }

  if (form.paymentMethod === "card_online" && !form.paymentProvider) {
    errors.paymentProvider = "Выберите платёжного провайдера.";
  }
}

function optionalString(value: string) {
  const normalized = value.trim();
  return normalized || null;
}
