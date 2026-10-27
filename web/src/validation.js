export function validateProfile(form, fieldDefinitions) {
  const errors = {};
  fieldDefinitions.forEach(([name, label]) => {
    if (form[name] === "") errors[name] = `${label} is required.`;
  });
  if (form.Age && (Number(form.Age) < 14 || Number(form.Age) > 120)) {
    errors.Age = "Enter an age between 14 and 120.";
  }
  return errors;
}
