use proc_macro::TokenStream;
use quote::{format_ident, quote};
use syn::{Data, DeriveInput, Field, Fields, Index, parse_macro_input};

/// Derives an implementation of the `PyGcTraverse` trait (only usable within the
/// `pydantic-core` crate).
///
/// Every field of the struct or enum is traversed, meaning every field type is required
/// to implement `PyGcTraverse` (plain data types have a no-op implementation, defined in
/// the `py_gc` module). Fields that should deliberately *not* be traversed must be
/// explicitly marked with the `#[py_gc(skip)]` attribute — which is only sound if the
/// field can never hold a strong reference to a Python object.
#[proc_macro_derive(PyGcTraverse, attributes(py_gc))]
pub fn derive_py_gc_traverse(input: TokenStream) -> TokenStream {
    expand(&parse_macro_input!(input as DeriveInput))
        .unwrap_or_else(syn::Error::into_compile_error)
        .into()
}

fn is_skipped(field: &Field) -> syn::Result<bool> {
    let mut skip = false;
    for attr in &field.attrs {
        if attr.path().is_ident("py_gc") {
            attr.parse_nested_meta(|meta| {
                if meta.path.is_ident("skip") {
                    skip = true;
                    Ok(())
                } else {
                    Err(meta.error("unsupported `py_gc` attribute; expected `skip`"))
                }
            })?;
        }
    }
    Ok(skip)
}

fn expand(input: &DeriveInput) -> syn::Result<proc_macro2::TokenStream> {
    let name = &input.ident;

    // Types of the traversed fields, used to add `where` predicates when the type is generic:
    let mut field_types = Vec::new();

    let body = match &input.data {
        Data::Struct(data) => {
            let mut statements = Vec::new();
            match &data.fields {
                Fields::Named(fields) => {
                    for field in &fields.named {
                        if !is_skipped(field)? {
                            let ident = &field.ident;
                            statements.push(quote! {
                                crate::py_gc::PyGcTraverse::py_gc_traverse(&self.#ident, visit)?;
                            });
                            field_types.push(&field.ty);
                        }
                    }
                }
                Fields::Unnamed(fields) => {
                    for (i, field) in fields.unnamed.iter().enumerate() {
                        if !is_skipped(field)? {
                            let index = Index::from(i);
                            statements.push(quote! {
                                crate::py_gc::PyGcTraverse::py_gc_traverse(&self.#index, visit)?;
                            });
                            field_types.push(&field.ty);
                        }
                    }
                }
                Fields::Unit => {}
            }
            quote! { #(#statements)* }
        }
        Data::Enum(data) => {
            let mut arms = Vec::new();
            for variant in &data.variants {
                let variant_ident = &variant.ident;
                match &variant.fields {
                    Fields::Named(fields) => {
                        let mut bindings = Vec::new();
                        let mut statements = Vec::new();
                        for field in &fields.named {
                            if !is_skipped(field)? {
                                let ident = &field.ident;
                                bindings.push(quote! { #ident });
                                statements.push(quote! {
                                    crate::py_gc::PyGcTraverse::py_gc_traverse(#ident, visit)?;
                                });
                                field_types.push(&field.ty);
                            }
                        }
                        arms.push(quote! {
                            Self::#variant_ident { #(#bindings,)* .. } => { #(#statements)* }
                        });
                    }
                    Fields::Unnamed(fields) => {
                        let mut bindings = Vec::new();
                        let mut statements = Vec::new();
                        for (i, field) in fields.unnamed.iter().enumerate() {
                            if is_skipped(field)? {
                                bindings.push(quote! { _ });
                            } else {
                                let binding = format_ident!("f{i}");
                                bindings.push(quote! { #binding });
                                statements.push(quote! {
                                    crate::py_gc::PyGcTraverse::py_gc_traverse(#binding, visit)?;
                                });
                                field_types.push(&field.ty);
                            }
                        }
                        arms.push(quote! {
                            Self::#variant_ident(#(#bindings),*) => { #(#statements)* }
                        });
                    }
                    Fields::Unit => arms.push(quote! { Self::#variant_ident => {} }),
                }
            }
            quote! { match self { #(#arms)* } }
        }
        Data::Union(_) => {
            return Err(syn::Error::new_spanned(
                input,
                "`PyGcTraverse` cannot be derived for unions",
            ));
        }
    };

    let mut generics = input.generics.clone();
    // If the type is generic, require `PyGcTraverse` on the traversed field types
    // (e.g. `PhantomData<T>: PyGcTraverse` for `EnumValidator<T>`):
    if generics.type_params().next().is_some() {
        let where_clause = generics.make_where_clause();
        for ty in &field_types {
            where_clause
                .predicates
                .push(syn::parse_quote! { #ty: crate::py_gc::PyGcTraverse });
        }
    }
    let (impl_generics, ty_generics, where_clause) = generics.split_for_impl();

    Ok(quote! {
        #[automatically_derived]
        impl #impl_generics crate::py_gc::PyGcTraverse for #name #ty_generics #where_clause {
            #[allow(unused_variables)]
            fn py_gc_traverse(&self, visit: &pyo3::PyVisit<'_>) -> Result<(), pyo3::PyTraverseError> {
                #body
                Ok(())
            }
        }
    })
}
