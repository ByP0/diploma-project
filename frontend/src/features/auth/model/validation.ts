export type FieldErrors<T extends string> = Partial<Record<T, string>>;

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{8,128}$/;

export function validateEmail(email: string) {
  const value = email.trim().toLowerCase();
  if (!value) {
    return "Введите email";
  }

  if (!emailPattern.test(value)) {
    return "Введите корректный email";
  }

  return null;
}

export function validatePassword(password: string) {
  if (!password) {
    return "Введите пароль";
  }

  if (!passwordPattern.test(password)) {
    return "Минимум 8 символов, заглавная и строчная буква, цифра и спецсимвол";
  }

  return null;
}

export function validateName(name: string) {
  const value = name.trim();
  if (!value) {
    return null;
  }

  if (value.length < 2) {
    return "Имя должно быть не короче 2 символов";
  }

  return null;
}

export function validateToken(token: string) {
  const value = token.trim();
  if (!value) {
    return "Введите токен";
  }

  if (value.length < 16) {
    return "Токен слишком короткий";
  }

  return null;
}
